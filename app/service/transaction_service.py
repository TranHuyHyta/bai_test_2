from inspect import signature
import os
import jwt
import psycopg2
import hashlib
import json
from app.enum.type_enum import TransactionType

key = os.getenv('SECRET_KEY', "secret")
conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

def post_transaction_create(jwt_token, merchant_id, amount, extra_data):
    id = decode_auth_token(jwt_token)
    # print(id)
    command_merchant_id = f"SELECT * FROM merchant WHERE merchant_id='{merchant_id}'"
    cur.execute(command_merchant_id)
    merchants = cur.fetchall()
    
    for merchant in merchants:
        merchant_account_id = merchant[1]
        # print(merchant_account_id)
        data = {
            "merchant_id": merchant_id,
            "amount": amount,
            "extra_data" : extra_data
        }
        data_json = json.dumps(data).encode('utf-8')
        signature = hashlib.md5(data_json).hexdigest()
        # print(id)
        # print(merchant_account_id)
        if id == merchant_account_id:
            
            command_insert = f"INSERT INTO transaction(merchant_id, income_account, amount, extra_data, signature, status) \
                VALUES('{merchant_id}','{merchant_account_id}','{amount}', '{extra_data}', '{signature}', '{TransactionType.INITIALIZED.value}') \
                RETURNING transaction_id"
            cur.execute(command_insert)
            conn.commit()
            # print(cur.fetchone())
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