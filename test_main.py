from decimal import Decimal
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import connection

DATABASE_URL_TEST = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL_TEST, connect_args={
                       "check_same_thread": False}, echo=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    connection.Base.metadata.drop_all(bind=engine)
    connection.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    user_common = connection.User(
        name="Jose Comum",
        cpf_cnpj="12345678901",
        email="jose.comum@example.com",
        balance=Decimal("1000.00"),
        phone="11987654321"
    )
    user_shopkeeper = connection.User(
        name="Maria Lojista",
        cpf_cnpj="12345678901234",
        email="maria.lojista@example.com",
        balance=Decimal("500.00"),
        phone="11912345678"
    )
    db.add_all([user_common, user_shopkeeper])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[connection.get_db] = override_get_db

    try:
        yield db
    finally:
        db.rollback()
        db.close()
        connection.Base.metadata.drop_all(bind=engine)


client = TestClient(app)

# ---------------------------
# TESTS
# ---------------------------


@patch("main.requests.get")
def test_successful_transaction(mock_get, db):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "success", "data": {"authorization": True}}

    transaction_data = {
        "cpf_cnpj_source": "12345678901",
        "cpf_cnpj_destination": "12345678901234",
        "value": 250.00
    }

    source_user = db.query(connection.User).filter_by(
        cpf_cnpj=transaction_data["cpf_cnpj_source"]).first()
    destination_user = db.query(connection.User).filter_by(
        cpf_cnpj=transaction_data["cpf_cnpj_destination"]).first()
    print(f"[BEFORE] {source_user.name}: {source_user.balance}")
    print(f"[BEFORE] {destination_user.name}: {destination_user.balance}")

    response = client.post("/transaction", json=transaction_data)
    assert response.status_code == 201

    source_user = db.query(connection.User).filter_by(
        cpf_cnpj=transaction_data["cpf_cnpj_source"]).first()
    destination_user = db.query(connection.User).filter_by(
        cpf_cnpj=transaction_data["cpf_cnpj_destination"]).first()
    print(f"[AFTER] {source_user.name}: {source_user.balance}")
    print(f"[AFTER] {destination_user.name}: {destination_user.balance}")

    response_data = response.json()
    assert response_data["cpf_cnpj_source"] == transaction_data["cpf_cnpj_source"]
    assert response_data["cpf_cnpj_destination"] == transaction_data["cpf_cnpj_destination"]
    assert response_data["value"] == transaction_data["value"]

    expected_source_balance = Decimal(
        "1000.00") - Decimal(transaction_data["value"])
    expected_destination_balance = Decimal(
        "500.00") + Decimal(transaction_data["value"])
    assert source_user.balance == expected_source_balance
    assert destination_user.balance == expected_destination_balance


def test_insufficient_balance(db):
    transaction_data = {
        "cpf_cnpj_source": "12345678901",
        "cpf_cnpj_destination": "12345678901234",
        "value": 1500.00
    }

    response = client.post("/transaction", json=transaction_data)

    assert response.status_code == 400
    assert "Insufficient balance" in response.text

    source_user = db.query(connection.User).filter_by(
        cpf_cnpj="12345678901").first()
    destination_user = db.query(connection.User).filter_by(
        cpf_cnpj="12345678901234").first()
    assert source_user.balance == Decimal("1000.00")
    assert destination_user.balance == Decimal("500.00")
