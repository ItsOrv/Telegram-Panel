import json
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

class AccountManager:
    def __init__(self):
        self.accounts = self.load_accounts()

    def load_accounts(self):
        accounts_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'accounts.json')
        if os.path.exists(accounts_path):
            with open(accounts_path, 'r') as f:
                return json.load(f)
        return {}

    def save_accounts(self):
        accounts_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'accounts.json')
        with open(accounts_path, 'w') as f:
            json.dump(self.accounts, f)

    async def add_account(self, phone_number, api_id, api_hash):
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.start(phone=phone_number)
        session_string = client.session.save()
        self.accounts[phone_number] = session_string
        self.save_accounts()
        await client.disconnect()

    async def remove_account(self, phone_number):
        if phone_number in self.accounts:
            del self.accounts[phone_number]
            self.save_accounts()
            return True
        return False

    async def get_client(self, phone_number):
        if phone_number in self.accounts:
            session_string = self.accounts[phone_number]
            return TelegramClient(StringSession(session_string), API_ID, API_HASH)
        return None
