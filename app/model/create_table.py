from app.enum.type_enum import TypeEnumAccount, TypeEnumTransaction
import psycopg2
import uuid
from 
def uuid_generate_v4():
    return uuid.uuid4()

def create_account_table():
    conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
    cur= conn.cursor()
    cur.execute("CREATE TYPE account_type AS ENUM ('merchant', 'personal', 'issuer');")
    cur.execute("CREATE TABLE IF NOT EXISTS account (id serial PRIMARY KEY, \
                                                    account_id VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL, \
                                                    merchant_id VARCHAR(100)  \
                                                    balance integer,\
                                                    account_type account_type);")
    conn.commit()
    cur.close()
    conn.close()
 
def create_merchant_table():
    conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS merchant (id serial PRIMARY KEY, \
                                                    account_id FOREIGN KEY (account_id) REFERENCES account(account_id), \
                                                    merchant_name VARCHAR(50), \
                                                    api_key VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL, \
                                                    merchant_url VARCHAR(100);")
    conn.commit()
    cur.close()
    conn.close()

def create_transaction_table():
    conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
    cur = conn.cursor()
    cur.execute("CREATE TYPE transacion_status AS ENUM ('INITIALIZED', 'CONFIRMED', 'VERIFIED', 'COMPLETED', 'CANCELED', 'EXPIRED', 'FAILED');")
    cur.execute("CREATE TABLE IF NOT EXISTS transaction (id serial PRIMARY KEY, \
                                                        transaction_id VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL, \
                                                        merchant_id FOREIGN KEY (account_id) REFERENCES account(account_id), \
                                                        income_account DEFAULT uuid_generate_v4() NOT NULL, \
                                                        outcome_account VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL,\
                                                        amount DOUBLE PRECISION,\
                                                        extra_data VARCHAR(100),\
                                                        signature VARCHAR(100),\
                                                        status transaction_status;")
                                
    conn.commit()
    cur.close()
    conn.close()