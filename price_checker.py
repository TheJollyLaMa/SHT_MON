import os
import json
import math
import logging
import requests
from config import w3, ERC20_ABI
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# Load Algebra V3 pool ABI
with open("abis/Quickswap_Algebra_V3_ABI.json") as f:
    algebra_v3_abi = json.load(f)

from config import w3, SHT_ADDRESS, USDC_ADDRESS

log_path = Path("data/price_log.jsonl")
log_path.parent.mkdir(exist_ok=True)

def get_live_usd_prices():
    eth_usd = None
    pol_usd = None

    # Fetch ETH price
    try:
        eth_response = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": "ethereum", "vs_currencies": "usd"})
        eth_response.raise_for_status()
        eth_data = eth_response.json()
        eth_usd = eth_data.get("ethereum", {}).get("usd")
        logging.info(f"CoinGecko ETH response: {eth_data}")
    except Exception as e:
        logging.warning(f"Failed to fetch ETH price: {e}")

    # Fetch POL price
    try:
        pol_response = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": "polygon-ecosystem-token", "vs_currencies": "usd"})
        pol_response.raise_for_status()
        pol_data = pol_response.json()
        pol_usd = pol_data.get("polygon-ecosystem-token", {}).get("usd")
        logging.info(f"CoinGecko POL response: {pol_data}")
    except Exception as e:
        logging.warning(f"Failed to fetch POL price: {e}")

    if eth_usd is None:
        eth_usd = -0.99  # fallback
        logging.warning("Using fallback ETH/USD price")
    if pol_usd is None:
        pol_usd = -0.99  # fallback
        logging.warning("Using fallback POL/USD price")

    return eth_usd, pol_usd

def fetch_price_from_pool(pool_env_var, label, base_token, eth_usd, pol_usd):
    try:
        pool_address_raw = os.getenv(pool_env_var)
        if not pool_address_raw:
            logging.error(f"{label} price fetch failed: {pool_env_var} not found in .env")
            return

        pool_address = w3.to_checksum_address(pool_address_raw)
        pool_contract = w3.eth.contract(address=pool_address, abi=algebra_v3_abi)

        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        global_state = pool_contract.functions.globalState().call()
        sqrt_price_x96 = global_state[0]

        sqrt_price = sqrt_price_x96 / (2 ** 96)
        price = sqrt_price ** 2
        
        # Fetch decimals for token0 and token1
        token0_contract = w3.eth.contract(address=token0, abi=ERC20_ABI)
        token1_contract = w3.eth.contract(address=token1, abi=ERC20_ABI)
        decimals0 = token0_contract.functions.decimals().call()
        decimals1 = token1_contract.functions.decimals().call()
        
        # Correct for decimal differences
        decimal_adjustment = 10 ** (decimals0 - decimals1)
        adjusted_price = price * decimal_adjustment
        
        liquidity = None
        try:
            liquidity = pool_contract.functions.liquidity().call()
        except Exception as liquidity_error:
            logging.warning(f"{label}: liquidity() not available: {liquidity_error}")

        # Determine direction: we want SHT as base token
        if token0.lower() == SHT_ADDRESS.lower():
            logging.info(f"{label}: 1 SHT = {adjusted_price:.6f} {base_token}")
            logging.info(f"{label}: 1 {base_token} = {1 / adjusted_price:.6f} SHT")
        elif token1.lower() == SHT_ADDRESS.lower():
            inv_price = 1 / adjusted_price
            logging.info(f"{label}: 1 SHT = {inv_price:.6f} {base_token}")
            logging.info(f"{label}: 1 {base_token} = {adjusted_price:.6f} SHT")
        else:
            logging.warning(f"{label}: Neither token0 nor token1 matches SHT")

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pair": label,
            "price_sht_per_" + base_token.lower(): float(adjusted_price),
            "price_" + base_token.lower() + "_per_sht": float(1 / adjusted_price),
            "pool_address": pool_address,
            "decimals": {
                "token0": decimals0,
                "token1": decimals1
            },
            "sqrt_price_x96": int(sqrt_price_x96),
            "liquidity": liquidity,
            "eth_usd": eth_usd if base_token == "ETH" else None,
            "pol_usd": pol_usd if base_token == "POL" else None
        }

        with log_path.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        logging.error(f"{label} price fetch failed: {e}")

def get_token_price_from_pool():
    eth_usd, pol_usd = get_live_usd_prices()
    logging.info(f"ETH/USD: {eth_usd}, POL/USD: {pol_usd}")
    fetch_price_from_pool("Quickswap_Algebra_V3_POOL_SHT-USDC_ADDRESS", "SHT/USDC", "USDC", eth_usd, pol_usd)
    fetch_price_from_pool("Quickswap_Algebra_V3_POOL_SHT-ETH_ADDRESS", "SHT/ETH", "ETH", eth_usd, pol_usd)
    fetch_price_from_pool("Quickswap_Algebra_V3_POOL_SHT-POL_ADDRESS", "SHT/POL", "POL", eth_usd, pol_usd)