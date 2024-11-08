import base64
import json
import re
from typing import cast

import requests
from ens.utils import get_abi_output_types
from eth_abi import abi
from web3 import Web3
from web3._utils.abi import named_tree
from web3._utils.contracts import decode_transaction_data
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3.middleware import geth_poa_middleware
from web3.types import ABIFunction

SUPPORT_CHAINS = {
    "ethereum": {
        "display_name": "Ethereum",
        "rpc": "https://cloudflare-eth.com",
        "etherscan_address_link": "https://etherscan.io/address/",
        "explorer_transaction_link": "https://etherscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 1,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "arbitrum": {
        "display_name": "Arbitrum",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "etherscan_address_link": "https://arbiscan.io/address/",
        "explorer_transaction_link": "https://arbiscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 42161,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "optimism": {
        "display_name": "Optimism",
        "rpc": "https://mainnet.optimism.io",
        "etherscan_address_link": "https://optimistic.etherscan.io/address/",
        "explorer_transaction_link": "https://optimistic.etherscan.io/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 10,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "base": {
        "display_name": "Base",
        "rpc": "https://mainnet.base.org",
        "etherscan_address_link": "https://basescan.org/address/",
        "explorer_transaction_link": "https://basescan.org/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 8453,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "linea": {
        "display_name": "Linea",
        "rpc": "https://rpc.linea.build",
        "etherscan_address_link": "https://lineascan.build/address/",
        "explorer_transaction_link": "https://lineascan.build/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "ETH",
        "chain_id": 59144,
        "coin": {
            "symbol": "ETH",
            "id": 1027,
        },
    },
    "mantle": {
        "display_name": "Mantle",
        "rpc": "https://rpc.mantle.xyz",
        "etherscan_address_link": "https://explorer.mantle.xyz/address/",
        "explorer_transaction_link": "https://explorer.mantle.xyz/tx/",
        "debank_address_link": "https://debank.com/profile/",
        "token_name": "MNT",
        "chain_id": 5000,
        "coin": {
            "symbol": "MNT",
            "id": 27075,
        },
    },
}

chain_id_name_mapping = {SUPPORT_CHAINS[chain_name]["chain_id"]: chain_name for chain_name in SUPPORT_CHAINS.keys()}

ERC20_ABI = """
  [{
    "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  }]
"""

ERC721_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC1155_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "id", "type": "uint256"},
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "accounts",
                "type": "address[]",
            },
            {"internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
        ],
        "name": "balanceOfBatch",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True,
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "uri",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def build_web3(provider):
    w3 = Web3(provider)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def verify_0_address(address):
    return set(address[2:]) == {"0"}


def get_debug_trace_transaction(traces):
    def prune_delegates(trace):
        while (
            trace.get("calls") and len(trace.get("calls")) == 1 and trace.get("calls")[0]["call_type"] == "delegatecall"
        ):
            trace = trace["calls"][0]
        if trace.get("calls"):
            for i, sub_call in enumerate(trace.get("calls")):
                trace["calls"][i] = prune_delegates(sub_call)

        return trace

    def promote_delegate_calls(node, parent=None, index=None):
        if "calls" in node:
            for i, sub_node in enumerate(node["calls"]):
                if sub_node:
                    promote_delegate_calls(sub_node, node, i)

        if node.get("call_type") == "delegatecall" and node.get("already_promoted") != True and parent is not None:
            parent.update(
                {
                    "delegate_address": parent["from"],
                    "already_promoted": True,
                }
            )
            parent["calls"][index] = {}

    def parse_trace_address(trace_address):
        if trace_address == "{}":
            return []
        return list(map(int, trace_address.strip("{}").split(",")))

    def add_trace_to_tree(node, trace, path):
        for step in path:
            if "calls" not in node:
                node["calls"] = []
            if len(node["calls"]) <= step:
                node["calls"].extend([{}] * (step + 1 - len(node["calls"])))
            node = node["calls"][step]

        node.update(trace)
        node["trace_address"] = path

    root = {}
    for trace in traces:
        path = parse_trace_address(trace["trace_address"])
        add_trace_to_tree(root, trace, path)

    return prune_delegates(root)


def generate_type_str(component):
    if component["type"] == "tuple[]":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")[]"
    elif component["type"] == "tuple":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")"
    else:
        return component["type"]


def convert_dict(input_item):
    if isinstance(input_item, dict):
        result = []
        for key, value in input_item.items():
            entry = {"name": key, "value": None, "type": None}
            if isinstance(value, (list, tuple, set)):
                entry["type"] = "list"
                entry["value"] = convert_dict(value)
            elif isinstance(value, dict):
                entry["type"] = "list"
                entry["value"] = convert_dict(value)
            elif isinstance(value, str):
                entry["type"] = "string"
                entry["value"] = value
            elif isinstance(value, int):
                entry["type"] = "int"
                entry["value"] = value
            else:
                entry["type"] = "unknown"
                entry["value"] = value

            result.append(entry)
        return result

    elif isinstance(input_item, (list, tuple, set)):
        return [convert_dict(item) for item in input_item]

    return input_item


def convert_bytes_to_hex(item):
    if isinstance(item, dict):
        return {key: convert_bytes_to_hex(value) for key, value in item.items()}
    elif isinstance(item, list):
        return [convert_bytes_to_hex(element) for element in item]
    elif isinstance(item, tuple):
        return tuple(convert_bytes_to_hex(element) for element in item)
    elif isinstance(item, set):
        return {convert_bytes_to_hex(element) for element in item}
    elif isinstance(item, bytes):
        return item.hex()
    else:
        return item


def decode_function(function_abi_json, data_str, output_str):
    if data_str is not None and len(data_str) > 0:
        input = decode_transaction_data(
            cast(ABIFunction, function_abi_json),
            data_str,
            normalizers=BASE_RETURN_NORMALIZERS,
        )
        input = convert_dict(convert_bytes_to_hex(input))
    else:
        input = []

    if output_str is not None and len(output_str) > 0:
        types = get_abi_output_types(cast(ABIFunction, function_abi_json))
        data = bytes.fromhex(output_str)
        value = abi.decode(types, data)
        output = named_tree(function_abi_json["outputs"], value)
        output = convert_dict(convert_bytes_to_hex(output))
    else:
        output = []
    return input, output


def decode_log_data(types, data_str):
    data_hex_str = bytes.fromhex(data_str)
    decoded_abi = abi.decode(types, data_hex_str)

    encoded_abi = []
    decoded_abi_real = []
    for index in range(len(types)):
        encoded_abi.append("0x" + abi.encode(types[index : index + 1], decoded_abi[index : index + 1]).hex())

        if types[index].startswith("byte"):
            if type(decoded_abi[index]) is tuple:
                encode_tuple = []
                for element in decoded_abi[index]:
                    encode_tuple.append("0x" + element.hex())
                decoded_abi_real.append(encode_tuple)
            else:
                decoded_abi_real.append("0x" + decoded_abi[index].hex())
        else:
            decoded_abi_real.append(str(decoded_abi[index]))

    return decoded_abi_real, encoded_abi


def is_eth_address(address):
    return Web3.is_address(address)


def is_eth_transaction_hash(hash):
    pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
    return bool(re.fullmatch(pattern, hash))


def to_checksum_address(address):
    return Web3.to_checksum_address(address)


def decode_data_url_to_json(data_url):
    mime, encoded_data = data_url.split(",", 1)
    if ";base64" in mime:
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
    else:
        decoded_data = encoded_data
    try:
        return json.loads(decoded_data)
    except Exception as e:
        print(e)
        return None


def http_transfer_uri(uri):
    if uri.startswith("ipfs"):
        return "https://ipfs.io/ipfs/" + uri[7:]
    elif uri.startswith("http"):
        return uri
    else:
        return None


def get_json_from_uri_by_http(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None
