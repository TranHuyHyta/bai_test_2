import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg2

from app.enum.type_enum import AccountType, TransactionType
from app.service.account_service import (get_account_token, post_account,
                                         post_account_topup)
from app.service.merchant_service import post_merchant
from app.service.transaction_service import (post_transaction_confirm,
                                             post_transaction_create,
                                             post_transaction_verify,
                                             post_transaction_cancel,
                                             transfer,
                                             decode_auth_token)

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

class ServiceHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type','text/json')
        self.end_headers()

    def get_data_sent(self):
        content_length = int(self.headers['Content-Length'])
        if content_length:
            input_json = self.rfile.read(content_length)
            input_data = json.loads(input_json)
        else:
            input_data = None
        return input_data

	#GET
    def do_GET(self):
        self._set_headers()
        if self.path.endswith('/'):
            pass
            
        if self.path.find('account') != -1 and self.path.find('token'):
            data_response = self.get_data_sent()
            account_id = data_response['account_id']
            # print(account_id)
            token = get_account_token(account_id)
            # print(token)
            output_data = {
                "token": token
            }
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))

    #POST
    def do_POST(self):
        self._set_headers()
        if self.path.endswith('/merchant/signup'):
            data_account_type = self.get_data_sent()
            merchant_name = data_account_type['merchant_name']
            merchant_url = data_account_type['merchant_url']
            #create merchant account
            account_id = post_account(AccountType.Merchant.value)
            cur.execute(f"SELECT * FROM account WHERE account_id = '{account_id[0]}'")
            account = cur.fetchone()
            id = account[1]
            
            merchant_id = post_merchant(id, merchant_name, merchant_url)
            
            #fetch created account from database
            cur.execute(f"SELECT * FROM merchant WHERE merchant_id='{merchant_id[0]}'")
            merchant = cur.fetchone()

            output_data = {
                "id": merchant[0],
                "account_id": merchant[1],
                "merchant_id": merchant[2],
                "merchant_name": merchant[3],
                "api_key": merchant[4],
                "merchant_url": merchant[5]
            }

            ouput_json = json.dumps(output_data)
            self.wfile.write(ouput_json.encode('utf-8'))

        if self.path.endswith('/account'):
            #fetch data from postman
            data_account_type = self.get_data_sent()
            account_type = data_account_type['account_type']
            account_id = post_account(account_type)

            #fetch created account from database
            cur.execute(f"SELECT * FROM account WHERE account_id = '{account_id[0]}'")
            account = cur.fetchone()
            
            # return {"account_id": row[1]}
            output_data = {"id": account[0],
                            "account_id": account[1],
                            "balance": account[2],
                            "account_type": account[3]}
            output_json = json.dumps(output_data)

            self.wfile.write(output_json.encode('utf-8'))
        
        if self.path.find('account') != -1 and self.path.find('topup'):
            data = self.get_data_sent()
            jwt_token = data['token']
            account_id = data['account_id']
            amount = data['amount']
            # print(jwt_token)
            topup = post_account_topup(jwt_token, account_id, amount)
    
            command_select = f"SELECT * FROM account WHERE account_id='{topup[0]}'"
            cur.execute(command_select)

            topup_account = cur.fetchone()
            output_data = {
                "id": topup_account[0],
                "account_id": topup_account[1],
                "balance": topup_account[2],
                "account_type": topup_account[3]
            }
            output_json = json.dumps(output_data)

            self.wfile.write(output_json.encode('utf-8'))

        if self.path.endswith('/transaction/create'):

            data = self.get_data_sent()
            jwt_token = data['token']
            merchant_id = data['merchant_id']
            amount = data['amount']
            extra_data = data['extra_data']
            try:
                transaction_create = post_transaction_create(jwt_token, merchant_id, amount, extra_data)
                
                command_select = f"SELECT * FROM transaction WHERE transaction_id='{transaction_create[0]}'"
                cur.execute(command_select)

                transaction = cur.fetchone()
            except:
                command_update = f"UPDATE transaction SET status='{TransactionType.FAILED.value}' WHERE merchant_id='{merchant_id}'"
                cur.execute(command_update)
                conn.commit()

                command_select = f"SELECT * FROM transaction WHERE merchant_id='{merchant_id}'"
                cur.execute(command_select)

                transaction = cur.fetchone()
                
            output_data = {
                "transaction_id": transaction[1],
                "merchant_id": transaction[2],
                "income_account": transaction[3],
                "outcome_account": transaction[4],
                "amount": transaction[5],
                "extra_data": transaction[6],
                "signature": transaction[7],
                "status": transaction[8]
            }
            output_json = json.dumps(output_data)

            self.wfile.write(output_json.encode('utf-8'))
        
        if self.path.endswith('/transaction/confirm'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']
            try:
                confirm = post_transaction_confirm(personal_token,transaction_id)
                # print(confirm)
                if confirm:
                    output_data = {
                        "code": "SUCCESS",
                        "message": "transaction confirmed"
                    }
                    output_json = json.dumps(output_data)

                    self.wfile.write(output_json.encode('utf-8'))
                else:
                    output_data = {
                                "code": "FAILED",
                                "message": "transaction failed"
                            }
                    output_json = json.dumps(output_data)
                    self.wfile.write(output_json.encode('utf-8'))
            except:
                command_update = f"UPDATE transaction SET status='{TransactionType.EXPIRED.value}'  WHERE merchant_id='{merchant_id}'"
                cur.execute(command_update)
                conn.commit()

                output_data = {
                            "code": "FAILED",
                            "message": "transaction expired"
                        }
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

        if self.path.endswith('/transaction/verify'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']

            personal_id = decode_auth_token(personal_token)

            command_select = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
            cur.execute(command_select)
            trans = cur.fetchone()
            
            merchant_account_id = trans[3]
            amount = trans[5]
            try:
                verify = post_transaction_verify(personal_token, transaction_id)
                
                if verify:
                    transfer_balance = transfer(personal_id, merchant_account_id, amount)
                    if transfer_balance:
                        command_update = f"UPDATE transaction SET status='{TransactionType.COMPLETED.value}' WHERE transaction_id='{transaction_id}'"
                        cur.execute(command_update)
                        conn.commit()
                        output_data = {
                            "code": "SUCCESS",
                            "message": "transaction completed"
                        }
                        output_json = json.dumps(output_data)

                        self.wfile.write(output_json.encode('utf-8'))
                else:
                    output_data = {
                            "code": "FAILED",
                            "message": "transaction failed"
                        }
                    output_json = json.dumps(output_data)

                    self.wfile.write(output_json.encode('utf-8'))
            except:
                command_update = f"UPDATE transaction SET status='{TransactionType.EXPIRED.value}'  WHERE transaction_id='{transaction_id}'"
                cur.execute(command_update)
                conn.commit()

                output_data = {
                            "code": "FAILED",
                            "message": "transaction expired"
                        }
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
        
        if self.path.endswith('/transaction/cancel'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']

            cancel = post_transaction_cancel(personal_token, transaction_id)
            
            if cancel:
                output_data = {
                            "code": "SUCCESS",
                            "message": "transaction canceled"
                        }
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

            else:   
                output_data = {
                            "code": "FAILED",
                            "message": "transaction failed to cancel"
                        }
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=ServiceHandler, port=8088):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Server running at localhost:8088...')
    httpd.serve_forever()

if __name__=="__main__":
    run()
