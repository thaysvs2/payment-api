from sqlalchemy.orm import Session, relationship, sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, TIMESTAMP, DECIMAL, func
from decimal import Decimal
from pydantic import BaseModel

db_url = "mysql+pymysql://root:root@localhost:3306/Db"

# Attempt to connect to the database and create a session
try:
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except SQLAlchemyError as e:
    print("Error connecting to the database: ", e)

Base = declarative_base()

# Database Models

# User model


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    cpf_cnpj = Column(String(14), nullable=False, unique=True)
    email = Column(String(200), nullable=False, unique=True)
    balance = Column(DECIMAL(10, 2), default=0.00)
    phone = Column(String(11), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


# Transaction model
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    source = relationship("User", foreign_keys=[source_id])
    destination = relationship("User", foreign_keys=[destination_id])

# Pydantic Models for API Endpoints


class TransactionCreate(BaseModel):
    cpf_cnpj_source: str
    cpf_cnpj_destination: str
    value: float


class BalancePush(BaseModel):
    cpf_cnpj_source: str
    value: float

# Database Operations

# Dependency to get a DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to decrease a user's balance


def decrease_balance(db: Session, cpf_cnpj: str, value: float):
    value = Decimal(value)
    user = db.query(User).filter(User.cpf_cnpj == cpf_cnpj).first()
    if user:
        user.balance -= value
        db.flush()
        return user.balance
    return None

# Function to increase a user's balance


def increase_balance(db: Session, cpf_cnpj: str, value: float):
    value = Decimal(value)
    user = db.query(User).filter(User.cpf_cnpj == cpf_cnpj).first()
    if user:
        user.balance += value
        db.flush()
        return user.balance
    return None

# Function to create a new transaction record


def create_transaction_record(db: Session, cpf_cnpj_source: str, cpf_cnpj_destination: str, value: float):
    value = Decimal(value)
    source_user = db.query(User).filter(
        User.cpf_cnpj == cpf_cnpj_source).first()
    destination_user = db.query(User).filter(
        User.cpf_cnpj == cpf_cnpj_destination).first()

    if source_user and destination_user:
        transaction = Transaction(
            source_id=source_user.id,
            destination_id=destination_user.id,
            value=value
        )
        db.add(transaction)
        db.flush()
        return transaction
    return None


if __name__ == "__main__":
    db = SessionLocal()

    transaction_record = create_transaction_record(
        db=db, cpf_cnpj_source="87978556330", cpf_cnpj_destination="87978556324", value=35.00)
    if transaction_record:
        print(
            f"Transaction created successfully with ID: {transaction_record.id}")
    else:
        print("Failed to create transaction.")
    db.close()
