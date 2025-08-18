# Script para criar um usuário de teste no banco de dados

import os
from decimal import Decimal
from dotenv import load_dotenv
from database.connection import User, SessionLocal, Base, engine

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def create_user_record(db_session, user_data):
    """
    Função para criar um novo usuário no banco de dados.
    """
    try:
        new_user = User(
            name=user_data["name"],
            cpf_cnpj=user_data["cpf_cnpj"],
            email=user_data["email"],
            balance=Decimal(user_data["balance"]),
            phone=user_data["phone"]
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        print(f"Usuário '{new_user.name}' criado com sucesso! ID: {new_user.id}")
        return new_user
    except Exception as e:
        db_session.rollback()
        print(f"Erro ao criar usuário: {e}")
        return None

if __name__ == "__main__":
    # Garante que as tabelas existem antes de tentar inserir dados
    print("Verificando a existência das tabelas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Dados do novo usuário para criar
    user_to_create = {
        "name": "Jane Smith",
        "cpf_cnpj": "11122233344",
        "email": "jane.smith@example.com",
        "balance": 5000.00,
        "phone": "11999998888"
    }
    
    print("Criando novo usuário de teste...")
    created_user = create_user_record(db, user_to_create)

    db.close()
    
    if created_user:
        print("Script concluído com sucesso.")
    else:
        print("Script finalizado com erros.")

