from dataclasses import dataclass
from datetime import datetime
from indexer.domain import Domain, FilterData

@dataclass
class ERC20Transfer(FilterData):
    token_address: str
    from_address: str
    to_address: str
    value: int
    block_number: int
    block_timestamp: datetime
    transaction_hash: str