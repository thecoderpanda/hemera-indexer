import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer, extract_transfer_from_log
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.erc20_token_transfer.domain.erc20_transfer_time import ERC20Transfer
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi_setting import ERC20_TRANSFER_EVENT

logger = logging.getLogger(__name__)

def _filter_erc20_transfers(logs: List[Log]) -> List[TokenTransfer]:
    token_transfers = []
    for log in logs:
        transfers = extract_transfer_from_log(log)
        token_transfers.extend([
            transfer for transfer in transfers 
            if transfer.token_type == "ERC20"
        ])
    return token_transfers

class ERC20TransferJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [ERC20Transfer]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger.debug("Full user defined config: %s", self.user_defined_config)
        
        self._contract_list = self.user_defined_config.get("contract_address", [])
        self.logger.info("ERC20 contracts to process %s", self._contract_list)

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=self._contract_list, 
                topics=[ERC20_TRANSFER_EVENT.get_signature()]
            )
        ]
        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        
        # Filter and process ERC20 transfers
        erc20_transfers = _filter_erc20_transfers(logs)
        
        # Convert to our domain model
        transfer_records = [
            ERC20Transfer(
                token_address=transfer.token_address,
                from_address=transfer.from_address,
                to_address=transfer.to_address,
                value=transfer.value,
                block_timestamp=transfer.block_timestamp,
                block_number=transfer.block_number,
                transaction_hash=transfer.transaction_hash,
            )
            for transfer in erc20_transfers
        ]

        # Collect the transfers
        self._collect_domains(transfer_records)

    def _process(self, **kwargs):
        pass