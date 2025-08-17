import os
import logging
from typing import List
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, FastAPI
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import requests
from twilio.rest import Client
from database import connection # The import statement is correct

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI()

# ----------------------------------------------------
# Design Pattern: Notification Strategy
# The API uses the .env file to choose which notification services to use.
# ----------------------------------------------------

def log_notification(user_name: str, message: str):
    """Terminal log notification strategy."""
    logging.info(f"Log: Notification to {user_name}: {message}")

def twilio_notification(number: str, message: str):
    """SMS notification strategy using Twilio."""
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    try:
        twilio_message = client.messages.create(
            body=message,
            from_="+12184233149",
            to=f"+55{number}",
        )
        logging.info(f"SMS sent successfully to {number}.")
        return twilio_message.body
    except Exception as e:
        logging.error(f"Error sending Twilio notification: {e}")
        return None

def mock_notification(cpf_cnpj: str, value: float):
    """Notification strategy using mock service."""
    try:
        response = requests.post("https://util.devi.tools/api/v1/notify", json={
            "recipient_cpf_cnpj": cpf_cnpj,
            "amount": value,
            "message": "Transaction received successfully!"
        })
        response.raise_for_status()
        logging.info("Notification sent successfully via mock service.")
        return True
    except requests.RequestException as e:
        logging.error(f"Error sending notification via mock: {e}")
        return False

# Dictionary of strategies
NOTIFIERS = {
    "log": log_notification,
    "twilio": twilio_notification,
    "mock": mock_notification
}

def dispatch_notifications(source_user: connection.User, destination_user: connection.User, transaction_value: float):
    """
    A central function that triggers notifications based on the .env configuration.
    It can be easily modified to use any combination of services.
    """
    # Reads the configuration, with 'log' as default if the variable does not exist
    enabled_notifiers = os.getenv("NOTIFIERS", "log").split(',')
    
    # Prepare the generic message
    message = f"A transaction of ${transaction_value} has been successfully completed for user {destination_user.name}"

    for notifier_type in enabled_notifiers:
        notifier_type = notifier_type.strip().lower()
        
        # Call the correct implementation
        if notifier_type == "log":
            NOTIFIERS[notifier_type](user_name=destination_user.name, message=message)
        elif notifier_type == "twilio":
            NOTIFIERS[notifier_type](number=destination_user.phone, message=message)
        elif notifier_type == "mock":
            NOTIFIERS[notifier_type](cpf_cnpj=destination_user.cpf_cnpj, value=transaction_value)

@app.post("/transaction", response_model=connection.TransactionCreate, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: connection.TransactionCreate, db: Session = Depends(connection.get_db)):
    logging.info("Starting transaction.")
    try:
        source_user = db.query(connection.User).filter(connection.User.cpf_cnpj == transaction.cpf_cnpj_source).first()
        destination_user = db.query(connection.User).filter(connection.User.cpf_cnpj == transaction.cpf_cnpj_destination).first()

        if not source_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source user not found.")
        if not destination_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination user not found.")

        if len(source_user.cpf_cnpj) == 14:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shopkeepers cannot make transactions.")

        if source_user.balance < transaction.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance.")

        logging.info("Consulting external authorization service.")
        authorizer_response = requests.get("https://util.devi.tools/api/v2/authorize")
        
        if authorizer_response.status_code != 200:
            logging.error(f"Authorizer returned an error status: {authorizer_response.status_code}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not authorized by the external service.")
        
        authorizer_data = authorizer_response.json()
        if authorizer_data.get("status") == "fail" or not authorizer_data.get("data", {}).get("authorization"):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not authorized by the external service.")

        logging.info("Transaction authorized. Performing database operations.")
        
        connection.decrease_balance(db, transaction.cpf_cnpj_source, transaction.value)
        connection.increase_balance(db, transaction.cpf_cnpj_destination, transaction.value)
        connection.create_transaction_record(db, cpf_cnpj_source=transaction.cpf_cnpj_source, cpf_cnpj_destination=transaction.cpf_cnpj_destination, value=transaction.value)
        
        db.commit()

        logging.info("Transaction successfully registered. Sending notifications.")
        
        # Triggers notifications according to configuration
        dispatch_notifications(source_user=source_user, destination_user=destination_user, transaction_value=transaction.value)
        
        return {
            "cpf_cnpj_source": transaction.cpf_cnpj_source,
            "cpf_cnpj_destination": transaction.cpf_cnpj_destination,
            "value": transaction.value
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")
    
    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error during the transaction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred. Please try again later.")

    finally:
        db.close()

@app.post("/add-balance", response_model=connection.BalancePush)
def add_balance(balance_data: connection.BalancePush, db: Session = Depends(connection.get_db)):
    logging.info("Increasing balance for the specified user.")
    try:
        connection.increase_balance(db=db, cpf_cnpj=balance_data.cpf_cnpj_source, value=balance_data.value)
        db.commit()
        logging.info("Success!")
        return {
            "cpf_cnpj_source": balance_data.cpf_cnpj_source,
            "value": balance_data.value
        }
    except Exception as e:
        db.rollback()
        logging.error(f"Something went wrong: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error adding balance: {e}")
    finally:
        db.close()
