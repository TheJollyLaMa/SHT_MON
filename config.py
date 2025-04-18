import os
import json
from dotenv import load_dotenv
from web3 import Web3
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# Connect to Polygon RPC
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Token addresses
SHT_ADDRESS = Web3.to_checksum_address(os.getenv("SHT_ADDRESS"))
USDC_ADDRESS = Web3.to_checksum_address(os.getenv("USDC_ADDRESS"))

log_path = Path("data/price_log.jsonl")
log_path.parent.mkdir(exist_ok=True)

with open('./abis/ERC-20_ABI.json', 'r') as abi_file:
    ERC20_ABI = json.load(abi_file)