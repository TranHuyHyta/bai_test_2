from app.model.create_table import create_table
import psycopg2
import uuid
import jwt
from app.enum.type_enum import AccountType
import os 

key = os.getenv('SECRET_KEY', "secret")
conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

_uuid = uuid.uuid4()

def post_account(type):
    command_insert = f"INSERT INTO account(balance, account_type) VALUES ('{0}', '{type}') RETURNING account_id"
    cur.execute(command_insert)
    conn.commit()
    return cur.fetchone()
    

def get_account_token(account_id):
    command_exe = f"SELECT * FROM account WHERE account_id='{account_id}'"
    cur.execute(command_exe)
    account = cur.fetchone()
    # print(type(account[1]))
    token = encode_auth_token(account[1])
    return token

def post_account_topup(auth_token, account_id, amount):
    # id from token
    id = decode_auth_token(auth_token)
    
    command_iusser_id = f"SELECT * FROM account WHERE account_type='issuer'" 
    cur.execute(command_iusser_id)
    issuers = cur.fetchall()
    for issuer in issuers:
        issuer_account_id = issuer[1]
        if id == issuer_account_id:
            # print(id)
            command_update = f"UPDATE account SET balance='{amount}' WHERE account_id='{account_id}' RETURNING account_id"
            cur.execute(command_update)
            conn.commit()
            return cur.fetchone()
        

def encode_auth_token(account_id: str):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'account_id': account_id
            }
            return jwt.encode(
                payload,
                key,
                algorithm='HS256'
            )
        except Exception as e:
            return e


def decode_auth_token(token: str):
    try:
        payload = jwt.decode(token, key, algorithms='HS256')
        return payload['account_id']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'