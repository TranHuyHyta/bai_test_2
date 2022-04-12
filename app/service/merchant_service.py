import os
import jwt
import psycopg2

key = os.getenv('SECRET_KEY', "secret")

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

def post_merchant(name, url):
    cur.execute(f"INSERT INTO merchant(merchant_name, merchant_url)\
                VALUES('{name}', '{url}') RETURNING merchant_id")
    conn.commit()
    return cur.fetchone()

def get_merchant_token(account_id):
    command_select_acc= f"SELECT * FROM account WHERE account_id='{account_id}'"
    cur.execute(command_select_acc)
    account = cur.fetchone()
    merchant_id = account[1]

    command_select_mer = f"SELECT * FROM merchant WHERE merchant_id='{merchant_id}'"
    cur.execute(command_select_mer)
    merchant = cur.fetchone()
    api_key = merchant[3]
    
    token = encode_auth_token(api_key)
    return token

def encode_auth_token(API_KEY: str):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'api_key': API_KEY
            }
            return jwt.encode(
                payload,
                key,
                algorithm='HS256'
            )
        except Exception as e:
            return e


def decode_merchant_auth_token(token: str):
    try:
        payload = jwt.decode(token, key, algorithms='HS256')
        return payload['api_key']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
