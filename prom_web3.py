from web3.middleware.geth_poa import geth_poa_middleware
from web3 import Web3
import random
import logging
from requests import Session
from requests.auth import HTTPProxyAuth
import time

from proxies import log

class TestnetProm:

    def __init__(self,
                private_key,
                rpc,
                session_proxies,
                proxi_auth,
        ):
        
        self.private_key = private_key

        self.proxi_auth = proxi_auth
        self.session = Session()
        self.session.proxies = session_proxies
        self.session.auth = HTTPProxyAuth(self.proxi_auth[0], self.proxi_auth[1])

        self.web3 = Web3(Web3.HTTPProvider(endpoint_uri=rpc, session=self.session))
        self.address = Web3.to_checksum_address(self.web3.eth.account.from_key(private_key=private_key).address)
        print(f'Proxies: [{self.session.proxies}]')


    def send_transaction(self,
                         to,
                         from_ = None,
                         data = None,
                         increase_gas = 1.1,
                         value = None
        ):
        
        if not from_:
            from_ = self.address
        
        tx_params = {
            'chainId': self.web3.eth.chain_id,
            'nonce': self.web3.eth.get_transaction_count(self.address),
            'from': Web3.to_checksum_address(from_),
            'to': Web3.to_checksum_address(to),
            'gasPrice': self.web3.eth.gas_price,

        }
        

        if data:
            tx_params['data'] = data

        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(self.web3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            print(f'{self.address} | transaction failed | {err}')
            return None

        sign = self.web3.eth.account.sign_transaction(tx_params, self.private_key)
        return self.web3.eth.send_raw_transaction(sign.rawTransaction)
    

    def verif_tx(self, tx_hash) -> bool:

        try: 
            data = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=100)
            if 'status' in data and data['status'] == 1:
                print(f'{self.address} | transaction was successful: {tx_hash.hex()}')
                return True
            else:
                print(f'{self.address} | transaction failed {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            print(f'{self.address} | unexpected error in <verif_tx> function: {err}')
            
            return False


def random_transaction_sender() -> str:
    w3 = Web3(Web3.HTTPProvider(endpoint_uri='https://prom-testnet.alt.technology/'))


    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    c = random.randint(0, 2)
    latest_block = w3.eth.get_block(w3.eth.block_number)

    transactions_hex = [tx.hex() for tx in latest_block['transactions']]

    transaction = w3.eth.get_transaction(transaction_hash=transactions_hex[c])
    sender = transaction['from']

    return sender


def main():
    cou = 0
    return_ = {

    }
    rpc = 'https://prom-testnet.alt.technology/'

    for k, v in log.items():
        try:
            cou += 1
            print(f"Акаунт {cou}: ")    
            time.sleep(3)

            user = TestnetProm(private_key=v[5],
                rpc=rpc,
                session_proxies={'http': f'http://{v[0]}:{v[1]}'},
                proxi_auth=[v[2], v[3]],
                )
                    
            print(f'Статус подключения к [{rpc}]: {user.web3.is_connected()}')
            for i in range(1, 6):
                rnds = random_transaction_sender()
                tx = user.send_transaction(to=rnds,
                                            from_=v[4],
                                            value=user.web3.to_wei(0.01, 'ether')
                                            )

                res = user.verif_tx(tx_hash=tx)
                print(res)

                if not res:
                    if cou not in return_:
                        return_[cou] = []
                    return_[cou].append(i)
                    print(return_)
        
        except Exception as err:
            print(err)
            continue


if __name__ == '__main__':
    main()



