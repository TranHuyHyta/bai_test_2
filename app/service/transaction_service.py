
import hashlib
import json
import os
import time

from app.decorator.timeout import timeout
from app.enum.type_enum import AccountType

import jwt
import psycopg2
from app.enum.type_enum import TransactionType

key = os.getenv('SECRET_KEY', "secret")
conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

@timeout(300)
def post_transaction_create(jwt_token, merchant_id, amount, extra_data):
    id = decode_merchant_auth_token(jwt_token)
    # time.sleep(10) #check delay
    # print(id)
    command_merchant_id = f"SELECT * FROM account WHERE merchant_id='{merchant_id}'"
    cur.execute(command_merchant_id)
    account = cur.fetchone()
    merchant_id = account[1]
    merchant_account_id = account[2]

    command_select_acc= f"SELECT * FROM merchant WHERE api_key='{id}'"
    cur.execute(command_select_acc)
    acc = cur.fetchone()
    mer_id = acc[1]

    data = {
        "merchant_id": merchant_id,
        "amount": amount,
        "extra_data" : extra_data
    }
    data_json = json.dumps(data).encode('utf-8')
    signature = hashlib.md5(data_json).hexdigest()

    if mer_id == merchant_id:
        command_insert = f"INSERT INTO transaction(merchant_id, income_account, amount, extra_data, signature, status) \
            VALUES('{merchant_id}','{merchant_account_id}','{amount}', '{extra_data}', '{signature}', '{TransactionType.INITIALIZED.value}') \
            RETURNING transaction_id"
        cur.execute(command_insert)
        conn.commit()
        return cur.fetchone()

@timeout(300)
def post_transaction_confirm(jwt_token, transaction_id):
    #decode personal account token
    id = decode_auth_token(jwt_token)
    # print(id)
    #check personal_id
    command_select_acc = f"SELECT * FROM account WHERE account_id='{id}'"
    cur.execute(command_select_acc)
    account = cur.fetchone()
    account_id = account[2]
    balance = account[3]
    # print(balance)

    command_select_trans = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
    cur.execute(command_select_trans)
    transaction = cur.fetchone()
    trans_amount = transaction[5]
    status = transaction[8]
    
    if status == TransactionType.INITIALIZED.value:
        print(status)
        if trans_amount > balance:
            print(trans_amount)
            print(balance)
            command_update_trans = f"UPDATE transaction SET status='{TransactionType.FAILED.value}' WHERE transaction_id='{transaction_id}"
            cur.execute(command_update_trans)
            conn.commit()
            return False
        else:
            command_update_trans = f"UPDATE transaction SET outcome_account='{account_id}', status='{TransactionType.CONFIRMED.value}' WHERE transaction_id='{transaction_id}'"
            cur.execute(command_update_trans)
            conn.commit()
            return True
    return False

@timeout(300)
def post_transaction_verify(jwt_token, transaction_id):
    id = decode_auth_token(jwt_token)
    
    command_select_acc = f"SELECT * FROM account WHERE account_id='{id}'"
    cur.execute(command_select_acc)
    account = cur.fetchone()
    balance = account[3]

    command_select_trans = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
    cur.execute(command_select_trans)
    transaction = cur.fetchone()
    trans_amount = transaction[5]
    status = transaction[8]

    if status == TransactionType.CONFIRMED.value:
        if trans_amount > balance:
            print(1)
            command_update_trans = f"UPDATE transaction SET status='{TransactionType.FAILED.value}' WHERE transaction_id='{transaction_id}'"
            cur.execute(command_update_trans)
            conn.commit()
            return False
        else:
            command_update_trans = f"UPDATE transaction SET status='{TransactionType.VERIFIED.value}' WHERE transaction_id='{transaction_id}'"
            cur.execute(command_update_trans)
            conn.commit()
            return True
    return False

def transfer(personal_account_id, merchant_account_id, amount):
    command_select_personal_acc = f"SELECT * FROM account WHERE account_id='{personal_account_id}'"
    cur.execute(command_select_personal_acc)
    personal= cur.fetchone()
    personal_id = personal[2]
    personal_balance = personal[3]
    personal_type = personal[4]
    # print(personal)
    if personal_type  == AccountType.Personal.value:
        command_select_merchant_acc = f"SELECT * FROM account WHERE merchant_id='{merchant_account_id}'"
        cur.execute(command_select_merchant_acc)
        merchant = cur.fetchone()
    
        merchant_account_id = merchant[2]
        merchant_balance = merchant[3]
        merchant_type = merchant[4]
        
        if merchant_type == AccountType.Merchant.value:
            transfer_money_per = personal_balance - amount
            transfer_money_mer = merchant_balance + amount
            
            command_transfer_per = f"UPDATE account SET balance='{transfer_money_per}' WHERE account_id='{personal_id}'"
            cur.execute(command_transfer_per)

            command_transfer_mer = f"UPDATE account SET balance='{transfer_money_mer}' WHERE account_id='{merchant_account_id}'"
            cur.execute(command_transfer_mer)
            conn.commit()
            return True
    return False

def post_transaction_cancel(jwt_token, transaction_id):
    id = decode_auth_token(jwt_token)

    command_select_trans = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
    cur.execute(command_select_trans)
    transaction = cur.fetchone()
    status = transaction[8]

    command_select_per = f"SELECT * FROM account WHERE account_id='{id}'"
    cur.execute(command_select_per)
    personal = cur.fetchone()
    personal_account_type = personal[4]
    
    if personal_account_type == AccountType.Personal.value:
        if status == TransactionType.CONFIRMED.value:
            command_update = f"UPDATE transaction SET status='{TransactionType.CANCELED.value}' WHERE transaction_id='{transaction_id}'"
            cur.execute(command_update)
            conn.commit()
            return True
    return False


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

def decode_merchant_auth_token(token: str):
        try:
            payload = jwt.decode(token, key, algorithms='HS256')
            return payload['api_key']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'