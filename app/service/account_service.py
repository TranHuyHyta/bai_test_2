import os
import uuid

import jwt
import psycopg2

key = os.getenv('SECRET_KEY', "secret")
conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

_uuid = uuid.uuid4()

def post_account_merchant(merchant_id, account_type):
    command_insert = f"INSERT INTO account(merchant_id, balance, account_type) VALUES ('{merchant_id}','{0}', '{account_type}') RETURNING account_id"
    cur.execute(command_insert)
    conn.commit()
    return cur.fetchone()

def post_account(account_type):
    command_insert = f"INSERT INTO account(balance, account_type) VALUES (0, '{account_type}') RETURNING account_id"
    cur.execute(command_insert)
    conn.commit()
    return cur.fetchone()

def get_account_token(account_id):
    command_exe = f"SELECT * FROM account WHERE account_id='{account_id}'"
    cur.execute(command_exe)
    account = cur.fetchone()
    
    token = encode_auth_token(account[2])
    return token

def post_account_topup(auth_token, account_id, amount):
    # id from token
    print(auth_token)
    id = decode_auth_token(auth_token)
    # print(id)
    command_iusser_id = f"SELECT * FROM account WHERE account_id='{id}'" 
    cur.execute(command_iusser_id)
    issuer = cur.fetchone()
    print(issuer)
    issuer_account_id = issuer[2]
    if id == issuer_account_id:
        command_update = f"UPDATE account SET balance='{amount}' WHERE account_id='{account_id}' RETURNING account_id"
        cur.execute(command_update)
        conn.commit()
        return cur.fetchone()
        

def encode_auth_token(account_id: str):
        """
        Generates the Auth Token
        :return: string
        """
        # print(account_id)
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
        print(payload)
        return payload['account_id']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
