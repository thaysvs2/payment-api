# 💳 Payment API

This is a back-end RESTful API developed with **FastAPI** and **SQLAlchemy** to simulate a simplified payment system.  

The project implements core functionalities like **user and shopkeeper management**, **secure money transfers**, **external service integration** for transaction authorization and notifications, and a **robust testing suite**.

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### ✅ Prerequisites
Make sure you have the following installed:
- Python 3.8+
- pip (Python package installer)
- PostgreSQL (database server)
- DBeaver or pgAdmin (database client tool)

---

### 1. Clone the Repository
```bash
git clone https://github.com/thaysvs2/payment-api.git
cd payment-api
2. Set up the Python Virtual Environment
Create and activate a virtual environment to manage project dependencies.

# Create the virtual environment
python -m venv enviroment

# Activate the virtual environment
# On Windows
.\enviroment\Scripts\activate
# On macOS/Linux
source enviroment/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory and add the following variables:
# PostgreSQL database connection string
# Format: postgresql://<user>:<password>@<host>:<port>/<database>
DB_URL="postgresql://postgres:postgres@localhost:5432/your_database_name"

# Notifiers to be used (separate multiple services with a comma)
# Options: log, mock, twilio
NOTIFIERS="log, mock, twilio"

# Twilio account details (only required if "twilio" is in NOTIFIERS)
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"

5. Create the Database Tables
Run the following SQL commands inside your PostgreSQL database:
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    cpf_cnpj VARCHAR(14) NOT NULL UNIQUE,
    email VARCHAR(200) NOT NULL UNIQUE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    phone VARCHAR(11) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    destination_id INT NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES users(id),
    FOREIGN KEY (destination_id) REFERENCES users(id)
);

6. Run the Application
Start the API server using Uvicorn:
uvicorn main:app --reload
The API documentation will be available at:
👉 http://127.0.0.1:8000/docs

⚙️ Project Structure
payment-api/
│── main.py                # Main application entry point
│── database/              # Database connection and models
│   └── connection.py
│── test_main.py           # Unit tests with pytest
│── .env                   # Environment variables
│── requirements.txt       # Project dependencies

🧪 Running Tests
Run all tests with:
pytest

✅ Implemented Features
User and Shopkeeper Models: Differentiates between two user types.

Unique Constraints: Enforces unique CPF/CNPJ and email addresses.

Money Transfer Logic: Allows money transfer between users and to shopkeepers.

Shopkeeper Restrictions: Prevents shopkeepers from initiating transfers.

Balance Validation: Checks for sufficient balance before a transaction.

External Service Integration: Integrates with mock services for transaction authorization and notifications.

Atomic Transactions: Ensures all operations are completed or rolled back.

RESTful API: Clean and well-structured API using FastAPI.

🛠️ Technologies Used
Python 3.10+

FastAPI: High-performance, easy-to-use API framework

SQLAlchemy: ORM and SQL toolkit

psycopg2: PostgreSQL driver for Python

Twilio: SMS notification service

python-dotenv: Environment variables management

Pytest: Testing framework

httpx: HTTP client for FastAPI tests
