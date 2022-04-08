
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
    id = decode_auth_token(jwt_token)
    time.sleep(10) #check delay
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
            time.sleep(5)
            # print(cur.fetchone())
            return cur.fetchone()

@timeout(300)
def post_transaction_confirm(jwt_token, transaction_id):
    #decode personal account token
    id = decode_auth_token(jwt_token)
    print(id)
    print(transaction_id)
    #check personal_id
    command_select_acc = "SELECT * FROM account WHERE account_type='personal'"
    cur.execute(command_select_acc)
    accounts = cur.fetchall()
    
    command_select_trans = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
    cur.execute(command_select_trans)
    transaction = cur.fetchone()
    trans_amount = transaction[5]
    status = transaction[8]
    
    for account in accounts:
        personal_id = account[1]
        balance = account[2]
        if id == personal_id:
            if status == TransactionType.INITIALIZED.value:
                if trans_amount > balance:
                    command_update_trans = f"UPDATE transaction SET status='{TransactionType.FAILED.value}' WHERE transaction_id='{transaction_id}"
                    cur.execute(command_update_trans)
                    conn.commit()
                    return False
                else:
                    command_update_trans = f"UPDATE transaction SET outcome_account='{personal_id}', status='{TransactionType.CONFIRMED.value}' WHERE transaction_id='{transaction_id}'"
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
    personal_id = account[1]
    balance = account[2]

    if id == personal_id:
        command_select_trans = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
        cur.execute(command_select_trans)
        transaction = cur.fetchone()
        trans_amount = transaction[5]
        status = transaction[8]
        if status == TransactionType.CONFIRMED.value:
            if trans_amount > balance:
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
    personal_id = personal[1]
    personal_balance = personal[2]
    personal_type = personal[3]
    
    if personal_type  == AccountType.Personal.value:
        print(merchant_account_id)
        command_select_merchant_acc = f"SELECT * FROM account WHERE account_id='{merchant_account_id}'"
        cur.execute(command_select_merchant_acc)
        merchant = cur.fetchone()
        print(merchant)

        merchant_id = merchant[1]
        merchant_balance = merchant[2]
        merchant_type = merchant[3]
        
        if merchant_type == AccountType.Merchant.value:
            transfer_money_per = personal_balance - amount
            transfer_money_mer = merchant_balance + amount
            
            command_transfer_per = f"UPDATE account SET balance='{transfer_money_per}' WHERE account_id='{personal_id}'"
            cur.execute(command_transfer_per)

            command_transfer_mer = f"UPDATE account SET balance='{transfer_money_mer}' WHERE account_id='{merchant_id}'"
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
    personal_account_type = personal[3]
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
