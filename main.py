import asyncio
import aiohttp

from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account

from concurrent.futures import ThreadPoolExecutor
from sys import platform
import uuid


headers = {
    'authority': 'z9c2d6140-z4b7d7573-gtw.z86770b17.prm.sh',
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/json',
    'origin': 'https://mint.mntge.io',
    'referer': 'https://mint.mntge.io/',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'vary': 'Origin'
}

w3 = Web3(Web3.HTTPProvider("https://rpc.builder0x69.io"))


def signature(self):
    encode_message = encode_defunct(text=self.message)
    return w3.eth.account.sign_message(signable_message=encode_message,
                                       private_key=self.wallet.privateKey.hex()).signature.hex()


class App:
    def __init__(self, email):
        self.wallet = Account.create()
        self.email = email
        self.data = {
            "message": self.message,
            "signature": self.signature(),
            "wallet": self.wallet.address
        }
    message = f"This signature is to ensure you are the owner of this wallet. {uuid.uuid4()}"

    def signature(self):
        encode_message = encode_defunct(text=self.message)
        return w3.eth.account.sign_message(signable_message=encode_message,
                                           private_key=self.wallet.privateKey.hex()).signature.hex()

    async def worker(self):
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                await session.post("https://z9c2d6140-z4b7d7573-gtw.z86770b17.prm.sh/api/getRegistrationDetails",
                                   json=self.data)

                self.data.update({"details": {'email': self.email, 'phone': ""}})
                await session.post("https://z9c2d6140-z4b7d7573-gtw.z86770b17.prm.sh/api/register", json=self.data)

                del self.data['details']
                resp = await session.post("https://z9c2d6140-z4b7d7573-gtw.z86770b17.prm.sh/api/getRegistrationDetails",
                                          json=self.data)

                if (await resp.json())['registered']:
                    print(f'{self.email} | registred')
                    with open('result.txt', 'a+') as file:
                        file.write(f"{self.wallet.privateKey.hex()}:{self.email}\n")
                else:
                    print(f'Already registered or invalid email | {self.email}')
            except Exception as exc:
                print(f'Unknown except: {exc}')


def create_data():
    accs = []
    with open("emails.txt", 'r') as file:
        emails = [row.strip().split(":")[0] for row in file]

    def create(email):
        acc = App(email)
        accs.append(acc)

    with ThreadPoolExecutor(max_workers=30) as wp_executor:
        wp_executor.map(create, emails)

    return accs


if __name__ == "__main__":
    acs_data = create_data()
    if platform != "win32":
        import uvloop
        uvloop.install()
        loop = uvloop.new_event_loop()
        tasks = [loop.create_task(acc.worker()) for acc in acs_data]
        loop.run_until_complete(asyncio.gather(*tasks))
    else:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        tasks = [loop.create_task(acc.worker()) for acc in acs_data]
        loop.run_until_complete(asyncio.gather(*tasks))
    print('End.')
