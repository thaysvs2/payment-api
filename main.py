from fastapi import Depends, HTTPException, status, FastAPI
from database import connection  # The import statement is correct
from sqlalchemy.exc import SQLAlchemyError
import os
from twilio.rest import Client
from dotenv import load_dotenv
import requests
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI()

# Function for Twilio notification


def send_message(number, message):
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    try:
        twilio_message = client.messages.create(
            body=message,
            from_="+12184233149",
            to=f"+55{number}",
        )
        logging.info(f"Notification sent successfully to {number}.")
        return twilio_message.body
    except Exception as e:
        # If the notification fails, we log the error but don't roll back the transaction
        logging.error(f"Error sending Twilio notification: {e}")
        return None

# Function for mock notification service


def notify_mock(cpf_cnpj, value):
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


@app.post("/transaction", response_model=connection.TransactionCreate, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: connection.TransactionCreate, db: connection.Session = Depends(connection.get_db)):
    logging.info("Starting transaction.")
    try:
        source_user = db.query(connection.User).filter(
            connection.User.cpf_cnpj == transaction.cpf_cnpj_source).first()
        destination_user = db.query(connection.User).filter(
            connection.User.cpf_cnpj == transaction.cpf_cnpj_destination).first()

        if not source_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source user not found.")
        if not destination_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Destination user not found.")

        if len(source_user.cpf_cnpj) == 14:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Shopkeepers cannot make transactions.")

        if source_user.balance < transaction.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance.")

        logging.info("Consulting external authorization service.")
        authorizer_response = requests.get(
            "https://util.devi.tools/api/v2/authorize")

        if authorizer_response.status_code != 200:
            logging.error(
                f"Authorizer returned an error status: {authorizer_response.status_code}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Transaction not authorized by the external service.")

        authorizer_data = authorizer_response.json()
        if authorizer_data.get("status") == "fail" or not authorizer_data.get("data", {}).get("authorization"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Transaction not authorized by the external service.")

        logging.info("Transaction authorized. Performing database operations.")

        connection.decrease_balance(
            db, transaction.cpf_cnpj_source, transaction.value)
        connection.increase_balance(
            db, transaction.cpf_cnpj_destination, transaction.value)
        connection.create_transaction_record(db, cpf_cnpj_source=transaction.cpf_cnpj_source,
                                             cpf_cnpj_destination=transaction.cpf_cnpj_destination, value=transaction.value)

        db.commit()

        logging.info(
            "Transaction successfully registered. Sending notifications.")

        # Send notifications
        notify_mock(cpf_cnpj=destination_user.cpf_cnpj,
                    value=transaction.value)
        send_message(number=source_user.phone,
                     message=f"Transaction in the amount of R$ {transaction.value} successfully completed for user {destination_user.name}")

        return {
            "cpf_cnpj_source": transaction.cpf_cnpj_source,
            "cpf_cnpj_destination": transaction.cpf_cnpj_destination,
            "value": transaction.value
        }

    except SQLAlchemyError as e:
        # In case of any database error, perform a rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

    except HTTPException:
        raise

    except Exception as e:
        # For any other exception, ensure rollback
        db.rollback()
        logging.error(f"Unexpected error during the transaction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An internal error occurred. Please try again later.")

    finally:
        # Close the database connection
        db.close()


@app.post("/add-balance", response_model=connection.BalancePush)
def add_balance(balance_data: connection.BalancePush, db: connection.Session = Depends(connection.get_db)):
    logging.info("Increasing balance for the specified user.")
    try:
        connection.increase_balance(
            db=db, cpf_cnpj=balance_data.cpf_cnpj_source, value=balance_data.value)
        db.commit()
        logging.info("Success!")
        return {
            "cpf_cnpj_source": balance_data.cpf_cnpj_source,
            "value": balance_data.value
        }
    except Exception as e:
        db.rollback()
        logging.error(f"Something went wrong: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Error adding balance: {e}")
    finally:
        db.close()
