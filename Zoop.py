import os
import json
import asyncio
import aiohttp
from datetime import datetime
from colorama import Fore, Style, init
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector

# 初始化 colorama
init(autoreset=True)

# 时区设置
wib = "Asia/Jakarta"

class ZoopBot:
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Sec-Ch-Ua": '"Chromium";v="133", "Microsoft Edge WebView2";v="133", "Not(A:Brand";v="99", "Microsoft Edge";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Referer": "https://tgapp.zoop.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "User-Agent": UserAgent().random,
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.auth_endpoint = "https://tgapi.zoop.com/api/oauth/telegram"
        self.spin_endpoint = "https://tgapi.zoop.com/api/users/spin"
        self.task_endpoint = "https://tgapi.zoop.com/api/tasks"
        self.token_path = "./token.txt"
        self.proxy_path = "./proxies.txt"
        self.log_file = "./bot_log.txt"
        self.retry_delay = 5000  # 5 seconds
        self.spin_delay_min = 2000  # 2 seconds
        self.spin_delay_max = 5000  # 5 seconds
        self.check_interval = 3600000  # 1 hour

    def clear_terminal(self):
        os.system("cls" if os.name == "nt" else "clear")

    def log(self, message):
        timestamp = datetime.now().strftime("%x %X %Z")
        log_entry = f"[{timestamp}] {message}"
        print(f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {message}")
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def welcome(self):
        print(
            f"""
        {Fore.GREEN}Auto Spin + Daily | Zoop Bot
            """
            f"""
        {Fore.YELLOW}By Airdrop Insider
            """
        )

    def load_tokens(self):
        if not os.path.exists(self.token_path):
            self.log(f"{Fore.RED}No token.txt found. Please create one.{Style.RESET_ALL}")
            return []

        with open(self.token_path, "r") as f:
            tokens = [line.strip() for line in f.readlines() if line.strip()]

        if not tokens:
            self.log(f"{Fore.RED}token.txt.txt is empty. Please add tokens.{Style.RESET_ALL}")
            return []

        self.log(f"{Fore.GREEN}Loaded {len(tokens)} tokens.{Style.RESET_ALL}")
        return tokens

    def load_proxies(self):
        if not os.path.exists(self.proxy_path):
            self.log(f"{Fore.RED}No proxies.txt found. Running without proxy.{Style.RESET_ALL}")
            return

        with open(self.proxy_path, "r") as f:
            self.proxies = [line.strip() for line in f.readlines() if line.strip()]

        if not self.proxies:
            self.log(f"{Fore.RED}proxies.txt is empty. Running without proxy.{Style.RESET_ALL}")
        else:
            self.log(f"{Fore.GREEN}Loaded {len(self.proxies)} proxies.{Style.RESET_ALL}")

    def get_next_proxy_for_account(self, email):
        if email not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.proxies[self.proxy_index]
            self.account_proxies[email] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[email]

    def rotate_proxy_for_account(self, email):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.account_proxies[email] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    async def get_access_token_and_info(self, query_id, proxy=None):
        payload = {"initData": query_id}
        connector = ProxyConnector.from_url(proxy) if proxy else None
        async with aiohttp.ClientSession(connector=connector, headers=self.headers) as session:
            try:
                async with session.post(self.auth_endpoint, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    token = data["data"]["access_token"]
                    info = data["data"]["information"]
                    self.log(f"Access token.txt retrieved for user: {info['username']}")
                    return token, info
            except Exception as e:
                self.log(f"Error getting access token.txt: {e}")
                raise

    async def check_daily_info(self, token, user_id, proxy=None):
        url = f"{self.task_endpoint}/{user_id}"
        connector = ProxyConnector.from_url(proxy) if proxy else None
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data["data"]["claimed"], data["data"]["dayClaim"]
            except Exception as e:
                self.log(f"Error checking daily info: {e}")
                raise

    async def claim_daily_task(self, token, user_id, proxy=None, index=1):
        url = f"{self.task_endpoint}/rewardDaily/{user_id}"
        payload = {"index": index}
        connector = ProxyConnector.from_url(proxy) if proxy else None
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            try:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    self.log(f"Daily task claimed: {data}")
                    return data
            except Exception as e:
                self.log(f"Error claiming daily task: {e}")
                raise

    async def perform_spin(self, token, user_id, proxy=None):
        payload = {"userId": user_id, "date": datetime.now().isoformat()}
        connector = ProxyConnector.from_url(proxy) if proxy else None
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            try:
                await asyncio.sleep(self.spin_delay_min / 1000)  # Random delay
                async with session.post(self.spin_endpoint, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    reward = data["data"]["circle"]["name"]
                    self.log(f"Spin completed! Reward: {reward}")
                    return data
            except Exception as e:
                self.log(f"Error performing spin: {e}")
                raise

    async def run_bot_for_user(self, query_id):
        user_id = self.parse_user_id_from_query(query_id)
        self.log(f"User ID extracted: {user_id}")

        proxy = self.get_next_proxy_for_account(user_id)
        self.log(f"Using proxy: {proxy}")

        while True:
            try:
                token, info = await self.get_access_token_and_info(query_id, proxy)
                spin_count = info["spin"]

                daily_claimed, day_claim = await self.check_daily_info(token, user_id, proxy)
                if not daily_claimed:
                    await self.claim_daily_task(token, user_id, proxy)
                    token, info = await self.get_access_token_and_info(query_id, proxy)
                    spin_count = info["spin"]
                else:
                    self.log("Daily task already claimed today.")

                if spin_count > 0:
                    await self.perform_spin(token, user_id, proxy)
                    spin_count -= 1
                    self.log(f"Remaining spins: {spin_count}")
                else:
                    self.log("No spin tickets available. Waiting for next check...")
                    await asyncio.sleep(self.check_interval / 1000)
                    token, info = await self.get_access_token_and_info(query_id, proxy)
                    spin_count = info["spin"]

            except Exception as e:
                self.log(f"Bot encountered an error: {e}")
                await asyncio.sleep(self.retry_delay / 1000)

    def parse_user_id_from_query(self, query_id):
        from urllib.parse import parse_qs
        params = parse_qs(query_id)
        user_data = params.get("user", [None])[0]
        if not user_data:
            raise ValueError("No user data found in query ID")
        return json.loads(user_data)["id"]

    async def run_bot(self):
        self.clear_terminal()
        self.welcome()
        self.load_proxies()
        tokens = self.load_tokens()

        if not tokens:
            return

        tasks = [self.run_bot_for_user(token) for token in tokens]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    bot = ZoopBot()
    asyncio.run(bot.run_bot())
