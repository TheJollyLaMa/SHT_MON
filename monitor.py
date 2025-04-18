import os
import time
import logging
from config import w3, SHT_ADDRESS, USDC_ADDRESS, ERC20_ABI
from price_checker import get_token_price_from_pool
from datetime import datetime
from pathlib import Path

log_path = Path("data/price_log.jsonl")
log_path.parent.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(filename='logs/sht_mon.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def get_token_info(token_address):
    contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    return symbol, decimals

def main():
    if not w3.is_connected():
        logging.error("Failed to connect to Polygon RPC")
        return

    logging.info("Connected to Polygon RPC")

    try:
        sht_symbol, sht_decimals = get_token_info(SHT_ADDRESS)
        usdc_symbol, usdc_decimals = get_token_info(USDC_ADDRESS)
        logging.info(f"{sht_symbol} decimals: {sht_decimals}")
        logging.info(f"{usdc_symbol} decimals: {usdc_decimals}")

        while True:
            get_token_price_from_pool()
            time.sleep(60)

    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()