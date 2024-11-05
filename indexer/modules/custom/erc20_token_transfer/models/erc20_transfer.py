from datetime import datetime
from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter

class ERC20TransferTime(HemeraModel):
    __tablename__ = "erc20_transfer_time"
    
    transaction_hash = Column(BYTEA, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    block_timestamp = Column(TIMESTAMP)
    block_number = Column(BIGINT)
    
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)
    
    @staticmethod
    def model_domain_mapping():
        return [{
            "domain": "ERC20Transfer",
            "conflict_do_update": False,
            "update_strategy": None,
            "converter": general_converter,
        }]

# Add useful indexes
Index(
    "erc20_transfer_time_block_timestamp_idx",
    desc(ERC20TransferTime.block_timestamp)
)

Index(
    "erc20_transfer_time_from_address_idx",
    ERC20TransferTime.from_address
)

Index(
    "erc20_transfer_time_to_address_idx",
    ERC20TransferTime.to_address
)