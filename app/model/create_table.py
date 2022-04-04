from app.enum.type_enum import TypeEnumAccount, TypeEnumTransaction
import psycopg2
import uuid

def uuid_generate_v4():
    return uuid.uuid4()

def create_account_table():
    conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
    cur= conn.cursor()
    cur.execute("CREATE TYPE account_type AS ENUM ('merchant', 'personal', 'issuer');")
    cur.execute("CREATE TABLE IF NOT EXISTS account (id serial PRIMARY KEY, \
                                                    account_id varchar(100) DEFAULT uuid_generate_v4() NOT NULL, \
                                                    username varchar(50), \
                                                    password varchar(100),\
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
                                                    merchant_name varchar(50), \
                                                    merchant_url varchar(100);")
    conn.commit()
    cur.close()
    conn.close()

def create_transaction_table():
    conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS transaction (id serial PRIMARY KEY, \
                                                        transaction_id varchar(100) DEFAULT uuid_generate_v4() NOT NULL, \
                                                        merchant_id FOREIGN KEY (account_id) REFERENCES account(account_id), \
                                                        income_account varchar(50), \
                                                        outcome_account varchar(100) DEFAULT uuid_generate_v4() NOT NULL,\
                                                        merchant_url varchar(100);")
    conn.commit()
    cur.close()
    conn.close()