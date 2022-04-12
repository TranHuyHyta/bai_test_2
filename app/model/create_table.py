import psycopg2

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()


def create_merchant_table():
    cur.execute("CREATE TABLE IF NOT EXISTS merchant (\
        id serial PRIMARY KEY, \
        merchant_id VARCHAR(100) UNIQUE DEFAULT uuid_generate_v4() NOT NULL, \
        merchant_name VARCHAR(50), \
        api_key VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL, \
        merchant_url VARCHAR(100));")
    conn.commit()

def create_account_table():
    cur.execute("CREATE TABLE IF NOT EXISTS account (\
        id serial PRIMARY KEY, \
        merchant_id VARCHAR(100) REFERENCES merchant(merchant_id),\
        account_id VARCHAR(100) UNIQUE DEFAULT uuid_generate_v4() NOT NULL, \
        balance DOUBLE PRECISION,\
        account_type VARCHAR(100) NOT NULL);")
    conn.commit()



def create_transaction_table():
    cur.execute("CREATE TABLE IF NOT EXISTS transaction (\
        id serial PRIMARY KEY, \
        transaction_id VARCHAR(100) DEFAULT uuid_generate_v4() NOT NULL, \
        merchant_id VARCHAR(100), \
        income_account VARCHAR(100), \
        outcome_account VARCHAR(100),\
        amount DOUBLE PRECISION,\
        extra_data VARCHAR(100),\
        signature VARCHAR(100),\
        status VARCHAR(100) NOT NULL,\
        created_at TIMESTAMP);")
    conn.commit()

def create_table():
    command_extension = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
    cur.execute(command_extension)
    create_merchant_table()
    create_account_table()
    create_transaction_table()
    cur.close()
    conn.close()

def checkTableExists(tablename):
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tablename.replace('\'', '\'\'')))
    if cur.fetchone()[0] == 1:
        # cur.close()
        return True

    # cur.close()
    return False

create_table()
