import psycopg2
from datetime import datetime, timedelta
import requests
from app.enum.type_enum import TransactionType

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

def check_transaction_expire():
    # get list transaction
    command_select = f"SELECT transaction_id, extra_data, created_at\
                        FROM transaction\
                        WHERE status='{TransactionType.INITIALIZED.value}' \
                        OR status='{TransactionType.CONFIRMED.value}' \
                        OR status='{TransactionType.VERIFIED.value}'"
    cur.execute(command_select)
    trans=cur.fetchall()

    if(len(trans)<=0):
        print ("no transaction found !!!")
        return
    # print(trans)/
    for tran in trans:
        # _datetime=datetime.strptime(str(tran[2]),"YYYY-MM-DD HH:MM:SS")
        if (datetime.now()- tran[2])> timedelta(minutes=5):
            # update transaction staus to expire
            command_update = f"UPDATE transaction\
                                SET status='expired'\
                                WHERE transaction_id='{tran[0]}'"
            cur.execute(command_update)
            conn.commit()

            # call api update order status
            requests.post("http:127.0.0.1:5000/update-order-status",
            {"order_id":tran[2], "status":"expired"})