import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg2

from app.enum.type_enum import AccountType, TransactionType
from app.service.account_service import (get_account_token, post_account, post_account_merchant,
                                         post_account_topup)
from app.service.merchant_service import post_merchant, get_merchant_token
from app.service.transaction_service import (post_transaction_confirm,
                                             post_transaction_create,
                                             post_transaction_verify,
                                             post_transaction_cancel,
                                             transfer,
                                             decode_auth_token)

conn = psycopg2.connect("dbname=test_db user=admin password=admin port=5432")
cur= conn.cursor()

class ServiceHandler(BaseHTTPRequestHandler):
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
        # self._set_headers()
        if self.path==('/'):
            pass
            
        elif self.path.find('account') != -1 and self.path.find('token'):
            # self._set_header
            data_response = self.get_data_sent()
            account_id = data_response['account_id']
            command_select = f"SELECT * FROM account WHERE account_id='{account_id}'"
            cur.execute(command_select)
            account = cur.fetchone()
            account_type = account[4]
            print(account_type)
            if account_type == AccountType.Merchant.value:
                token = get_merchant_token(account_id)
            else:
                token = get_account_token(account_id)
            # print(token)
            output_data = {
                "token": token
            }
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))

    #POST
    def do_POST(self):
        
        if self.path==('/merchant/signup'):
            data_account_type = self.get_data_sent()
            merchant_name = data_account_type['merchant_name']
            merchant_url = data_account_type['merchant_url']
            #create merchant account
            merchant = post_merchant(merchant_name, merchant_url)
            merchant_id = merchant[0]
            
            account = post_account_merchant(merchant_id, AccountType.Merchant.value)
            account_id=account[0]

            #fetch created account from database
            cur.execute(f"SELECT * FROM merchant WHERE merchant_id='{merchant_id}'")
            merchant = cur.fetchone()

            output_data = {
                "merchant_name": merchant[2],
                "account_id": account_id,
                "merchant_id": merchant[1],
                "api_key": merchant[3],
                "merchant_url": merchant[4]
            }
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            ouput_json = json.dumps(output_data)
            self.wfile.write(ouput_json.encode('utf-8'))

        elif self.path==('/account'):
            #fetch data from postman
            data_account_type = self.get_data_sent()
            account_type = data_account_type['account_type']

            account_id = post_account(account_type)
            
            output_data = {
                            "account_id": account_id[0],
                            "balance": 0,
                            "account_type": account_type}
            output_json = json.dumps(output_data)
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(output_json.encode('utf-8'))
        
        elif self.path.find('account') != -1 and self.path.find('topup'):
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
                "account_id": topup_account[2],
                "balance": topup_account[3],
                "account_type": topup_account[4]
            }
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            output_json = json.dumps(output_data)

            self.wfile.write(output_json.encode('utf-8'))

        elif self.path==('/transaction/create'):

            data = self.get_data_sent()
            jwt_token = data['token']
            merchant_id = data['merchant_id']
            amount = data['amount']
            extra_data = data['extra_data']
            try:
                # print(1)
                transaction_create = post_transaction_create(jwt_token, merchant_id, amount, extra_data)

                command_select = f"SELECT * FROM transaction WHERE transaction_id='{transaction_create[0]}'"
                cur.execute(command_select)

                transaction = cur.fetchone()
            except:
                command_update = f"UPDATE transaction SET status='{TransactionType.EXPIRED.value}' WHERE merchant_id='{merchant_id}'"
                cur.execute(command_update)
                conn.commit()

                command_select = f"SELECT * FROM transaction WHERE merchant_id='{merchant_id}'"
                cur.execute(command_select)

                transaction = cur.fetchone()
            print(transaction)
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
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            output_json = json.dumps(output_data)

            self.wfile.write(output_json.encode('utf-8'))
        
        elif self.path==('/transaction/confirm'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']
            try:
                confirm = post_transaction_confirm(personal_token,transaction_id)
                if confirm:
                    output_data = {
                        "code": "SUCCESS",
                        "message": "transaction confirmed"
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    output_json = json.dumps(output_data)

                    self.wfile.write(output_json.encode('utf-8'))
                else:
                    output_data = {
                                "code": "FAILED",
                                "message": "transaction failed"
                            }
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    output_json = json.dumps(output_data)
                    self.wfile.write(output_json.encode('utf-8'))
            except:
                # self.send_response(404)
                command_update = f"UPDATE transaction SET status='{TransactionType.EXPIRED.value}'  WHERE transaction_id='{transaction_id}'"
                cur.execute(command_update)
                conn.commit()

                output_data = {
                            "code": "FAILED",
                            "message": "transaction expired"
                        }
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

        elif self.path==('/transaction/verify'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']

            personal_id = decode_auth_token(personal_token)

            command_select = f"SELECT * FROM transaction WHERE transaction_id='{transaction_id}'"
            cur.execute(command_select)
            trans = cur.fetchone()
            
            merchant_account_id = trans[2]
            print(merchant_account_id)
            amount = trans[5]
            try:
                verify = post_transaction_verify(personal_token, transaction_id)
                if verify:
                    print(1)
                    transfer_balance = transfer(personal_id, merchant_account_id, amount)
                    if transfer_balance:
                        command_update = f"UPDATE transaction SET status='{TransactionType.COMPLETED.value}' WHERE transaction_id='{transaction_id}'"
                        cur.execute(command_update)
                        conn.commit()
                        output_data = {
                            "code": "SUCCESS",
                            "message": "transaction completed"
                        }
                        self.send_response(200)
                        self.send_header('Content-type','application/json')
                        self.end_headers()
                        output_json = json.dumps(output_data)

                        self.wfile.write(output_json.encode('utf-8'))
                else:
                    
                    command_update = f"UPDATE transaction SET status='{TransactionType.FAILED.value}' WHERE transaction_id='{transaction_id}'"
                    cur.execute(command_update)
                    conn.commit()
                    output_data = {
                            "code": "FAILED",
                            "message": "transaction failed"
                        }
                    self.send_response(404)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
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
                self.send_response(404)
                self.send_header('Content-type','application/json')
                self.end_headers()
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
        
        elif self.path==('/transaction/cancel'):
            data = self.get_data_sent()
            personal_token = data['token']
            transaction_id = data['transaction_id']

            cancel = post_transaction_cancel(personal_token, transaction_id)
            
            if cancel:
                output_data = {
                            "code": "SUCCESS",
                            "message": "transaction canceled"
                        }
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

            else:   
                output_data = {
                            "code": "FAILED",
                            "message": "transaction failed to cancel"
                        }

                self.send_response(404)
                self.send_header('Content-type','application/json')
                self.end_headers()
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=ServiceHandler, port=8088):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Server running at localhost:8088...')
    httpd.serve_forever()

if __name__=="__main__":
    run()
