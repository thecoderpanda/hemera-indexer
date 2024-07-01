import json

from eth_abi import abi
from web3 import Web3
from web3.exceptions import Web3ValidationError

from domain.token import format_token_data
from domain.token_transfer import extract_transfer_from_log, \
    format_erc20_token_transfer_data, format_erc721_token_transfer_data, format_erc1155_token_transfer_data
from enumeration.entity_type import EntityType
from enumeration.token_type import TokenType
from exporters.console_item_exporter import ConsoleItemExporter
from exporters.jdbc.schema.tokens import Tokens
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.enrich import enrich_token_transfer_type
from utils.json_rpc_requests import generate_eth_call_json_rpc
from utils.utils import rpc_response_to_result

erc_token_abi = {
    "ELSE": [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }],
    "ERC1155": [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "id", "type": "uint256"}],
            "name": "tokenSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
}

erc_abi_names = {
    "ELSE": [abi_fn['name'] for abi_fn in erc_token_abi["ELSE"]],
    "ERC1155": [abi_fn['name'] for abi_fn in erc_token_abi["ERC1155"]]
}


class ExportTokensAndTransfersJob(BaseJob):
    def __init__(
            self,
            index_keys,
            entity_types,
            web3,
            service,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)

        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter
        self._exist_token = get_exist_token(service)

    def _start(self):
        super()._start()

    def _collect(self):
        self._batch_work_executor.execute(self._data_buff['enriched_log'], self._collect_batch)
        self._batch_work_executor.shutdown()

    def _collect_batch(self, logs):

        tokens_parameter, token_transfers = extract_parameters_and_token_transfers(self._exist_token, logs)

        tokens, tokens_type = tokens_rpc_requests(self._web3,
                                                  self._batch_web3_provider.make_request,
                                                  tokens_parameter,
                                                  self._is_batch)

        for token in tokens:
            token['item'] = 'token'
            self._collect_item(token)

        for transfer_event in enrich_token_transfer_type(token_transfers, tokens_type):
            transfer_event['item'] = 'token_transfer'
            self._collect_item(transfer_event)

    def _process(self):
        (self._data_buff['erc20_token_transfers'],
         self._data_buff['erc721_token_transfers'],
         self._data_buff['erc1155_token_transfers']) = split_token_transfers(self._data_buff['token_transfer'])

        self._data_buff['formated_token'] = [format_token_data(token) for token in self._data_buff['token']]

        self._data_buff['erc20_token_transfers'] = sorted(self._data_buff['erc20_token_transfers'],
                                                          key=lambda x: (
                                                              x['block_number'],
                                                              x['transaction_hash'],
                                                              x['log_index']))

        self._data_buff['erc721_token_transfers'] = sorted(self._data_buff['erc721_token_transfers'],
                                                           key=lambda x: (
                                                               x['block_number'],
                                                               x['transaction_hash'],
                                                               x['log_index']))

        self._data_buff['erc1155_token_transfers'] = sorted(self._data_buff['erc1155_token_transfers'],
                                                            key=lambda x: (
                                                                x['block_number'],
                                                                x['transaction_hash'],
                                                                x['log_index']))

    def _export(self):
        items = []

        if self._entity_types & EntityType.TOKEN:
            items.extend(self._extract_from_buff(['formated_token']))

        if self._entity_types & EntityType.TOKEN_TRANSFER:
            items.extend(
                self._extract_from_buff(['erc20_token_transfers', 'erc721_token_transfers', 'erc1155_token_transfers']))

        self._item_exporter.export_items(items)


def get_exist_token(db_service):
    session = db_service.get_service_session()
    try:
        result = session.query(Tokens.address, Tokens.token_type).all()
        history_token = {}
        if result is not None:
            for item in result:
                history_token[item[0].hex()] = item[1]
    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return history_token


def extract_parameters_and_token_transfers(exist_tokens, logs):
    token_transfer = []
    for log in logs:
        transfer_event = extract_transfer_from_log(log)
        if transfer_event is not None:
            if type(transfer_event) is list:
                token_transfer.extend(transfer_event)
            else:
                token_transfer.append(transfer_event)

    new_tokens = set()
    for token in token_transfer:
        if token['tokenAddress'][2:] not in exist_tokens.keys():
            new_tokens.add((token['tokenAddress'], token['tokenType']))
        elif token['tokenType'] is None:
            token['tokenType'] = exist_tokens[token['tokenAddress'][2:]]

    tokens_parameter = []
    for token in new_tokens:
        tokens_parameter.append(
            {
                "address": token[0],
                "token_type": token[1]
            }
        )

    return tokens_parameter, token_transfer


def build_rpc_method_data(web3, tokens, fn):
    parameters = []

    for token in tokens:
        token_type = token['token_type'] if 'token_type' in token and token['token_type'] is not None else "ELSE"
        try:
            token['param_to'] = token['address']
            token['param_data'] = (web3.eth
                                   .contract(address=Web3.to_checksum_address(token['address']),
                                             abi=erc_token_abi[token_type])
                                   .encodeABI(fn_name=fn))
            for abi_fn in erc_token_abi[token_type]:
                if fn == abi_fn['name']:
                    token['data_type'] = abi_fn['outputs'][0]['type']

        except Web3ValidationError:
            token['data'] = '0x'
            token['data_type'] = ''
        parameters.append(token)

    return parameters


def tokens_rpc_requests(web3, make_requests, tokens, is_batch):
    if len(tokens) == 0:
        return [], {}
    fn_names = ['name', 'symbol', 'decimals', 'totalSupply', 'tokenSupply']

    for fn_name in fn_names:
        token_name_rpc = list(generate_eth_call_json_rpc(build_rpc_method_data(web3, tokens, fn_name)))

        if is_batch:
            response = make_requests(params=json.dumps(token_name_rpc))
        else:
            response = [make_requests(params=json.dumps(token_name_rpc[0]))]

        for data in list(zip(response, tokens)):
            result = rpc_response_to_result(data[0], ignore_errors=True)

            token = data[1]
            value = result[2:] if result is not None else None
            try:
                token[fn_name] = abi.decode([token['data_type']], bytes.fromhex(value))[0]
                if token['data_type'] == 'string':
                    token[fn_name] = token[fn_name].replace('\u0000', '')
            except Exception as e:
                token[fn_name] = None

    token_types = {}
    for token in tokens:
        if token['token_type'] is None:
            if token['decimals'] is not None:
                # if token['decimals'] is not None and token['decimals'] > 0:
                token['token_type'] = TokenType.ERC20.value
            else:
                token['token_type'] = TokenType.ERC721.value
            token_types[token['address']] = token['token_type']

    return tokens, token_types


def split_token_transfers(token_transfers):
    erc20_token_transfers = []
    erc721_token_transfers = []
    erc1155_token_transfers = []

    for token_transfer in token_transfers:
        if token_transfer['tokenType'] == TokenType.ERC20.value:
            erc20_token_transfers.append(format_erc20_token_transfer_data(token_transfer))
        elif token_transfer['tokenType'] == TokenType.ERC721.value:
            erc721_token_transfers.append(format_erc721_token_transfer_data(token_transfer))
        elif token_transfer['tokenType'] == TokenType.ERC1155.value:
            erc1155_token_transfers.append(format_erc1155_token_transfer_data(token_transfer))

    return erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers
