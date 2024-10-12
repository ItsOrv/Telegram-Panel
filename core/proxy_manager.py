import json
import os
import random

class ProxyManager:
    def __init__(self):
        self.proxies = self.load_proxies()

    def load_proxies(self):
        proxies_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.json')
        if os.path.exists(proxies_path):
            with open(proxies_path, 'r') as f:
                return json.load(f)
        return []

    def save_proxies(self):
        proxies_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.json')
        with open(proxies_path, 'w') as f:
            json.dump(self.proxies, f)

    def add_proxy(self, proxy):
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.save_proxies()
            return True
        return False

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.save_proxies()
            return True
        return False

    def get_random_proxy(self):
        return random.choice(self.proxies) if self.proxies else None
