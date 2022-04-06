import psycopg2
import uuid

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

def post_merchant(account_id, name, url):
    # command_get_account_id = "SELECT account_id FROM account"
    # account_id = cur.execute(command_get_account_id)
    # print(account_id)
    cur.execute(f"INSERT INTO merchant(account_id, merchant_name, merchant_url)\
                VALUES('{account_id}', '{name}', '{url}') RETURNING merchant_id")
    conn.commit()
    return cur.fetchone()
