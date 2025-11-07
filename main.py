import requests
import random
import concurrent.futures
from typing import Dict, Optional

def load_proxies(proxy_file):
    proxies = []
    try:
        with open(proxy_file, "r") as file:
            for line in file:
                proxy_parts = line.strip().split(":")
                if len(proxy_parts) == 4:
                    ip, port, username, password = proxy_parts
                    proxy_url = f"http://{username}:{password}@{ip}:{port}"
                    proxies.append({"http": proxy_url, "https": proxy_url})
        return proxies
    except FileNotFoundError:
        print(f"The file '{proxy_file}' was not found.")
        return []
    except Exception as e:
        print(f"Error loading proxies: {e}")
        return []

def get_doge_balance(address: str, proxy: Optional[Dict] = None) -> Optional[float]:
    try:
        url = f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/balance"
        response = requests.get(url, proxies=proxy, timeout=10)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('balance', 0) / 1e8
            return balance
        else:
            print(f"Failed to fetch balance for {address}. Status Code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balance for {address} using proxy {proxy}: {e}")
        return None

def process_address(address: str, proxies: list) -> tuple:
    proxy = random.choice(proxies) if proxies else None
    print(f"Fetching balance for {address} using proxy: {proxy}")
    balance = get_doge_balance(address, proxy)
    if balance is None:
        print(f"Retrying without proxy for address: {address}")
        balance = get_doge_balance(address)   
    return address, balance

def main():
    proxies = load_proxies("proxy.txt")
    if not proxies:
        print("No proxies loaded. Exiting.")
        return

    with open("doge.txt", "r") as file:
        addresses = [line.strip() for line in file if line.strip()]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_address = {
            executor.submit(process_address, address, proxies): address 
            for address in addresses
        }
        
        with open("dogebalance.txt", "a") as balance_file:
            for future in concurrent.futures.as_completed(future_to_address):
                address, balance = future.result()
                if balance is not None and balance > 0:
                    result_line = f"{address} | Balance: {balance} DOGE\n"
                    balance_file.write(result_line)
                    balance_file.flush() 
                    print(f"Address: {address} | Balance: {balance} DOGE (Saved to dogebalance.txt)")

if __name__ == "__main__":
    main()
