Payment API
This is a back-end RESTful API developed with FastAPI and SQLAlchemy to simulate a simplified payment system. The project implements core functionalities like user and shopkeeper management, secure money transfers, external service integration for transaction authorization and notifications, and a robust testing suite.

🚀 Getting Started
Follow these steps to set up and run the project locally.

Prerequisites
Make sure you have the following installed:

Python 3.8+

pip (Python package installer)

1. Clone the repository
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
Install all the required Python packages from the requirements.txt file.

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory and add the following variables. These are used for database connection and the Twilio notification service.

# Database connection string
DB_URL="mysql+pymysql://user:password@localhost:3306/your_database_name"

# Twilio account details
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
MEU_NUMERO="your_verified_phone_number"

5. Run the Application
You can start the API server using Uvicorn. The --reload flag enables auto-reloading on code changes.

uvicorn main:app --reload

The API documentation will be available at http://127.0.0.1:8000/docs.

⚙️ Project Structure
The project is organized into the following directories:

main.py: The main application entry point, defining all API endpoints and business logic.

database/: Contains the connection.py module for database management, including SQLAlchemy models and helper functions.

test_main.py: Contains unit tests for the API endpoints using pytest and FastAPI TestClient.

.env: Environment variables file.

requirements.txt: List of project dependencies.

🧪 Running Tests
The project includes a robust suite of unit tests to ensure all business logic is working correctly.

# Run all tests
pytest

✅ Implemented Features
User and Shopkeeper Models: Differentiates between two user types.

Unique Constraints: Enforces unique CPF/CNPJ and email addresses.

Money Transfer Logic: Allows money transfer between users and to shopkeepers.

Lojista Restrictions: Prevents shopkeepers from initiating transfers.

Balance Validation: Checks for sufficient balance before a transaction.

External Service Integration: Integrates with mock services for transaction authorization and payment notifications.

Atomic Transactions: Ensures that all database operations within a transaction are completed or rolled back in case of an error.

RESTful API: Provides a clean and well-structured API using FastAPI.

🛠️ Technologies Used
Python 3.10+

FastAPI: High-performance, easy-to-use API framework.

SQLAlchemy: Powerful Python SQL toolkit and Object Relational Mapper (ORM).

Twilio: Third-party service for sending SMS notifications.

python-dotenv: Manages environment variables.

Pytest: Framework for writing and running tests.

httpx: The recommended library for making HTTP requests with FastAPI's TestClient.
