from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class ERC1155TokenTransfers(HemeraModel):
    __tablename__ = "erc1155_token_transfers"

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    token_id = Column(NUMERIC(100), primary_key=True)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ERC1155TokenTransfer",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "erc1155_token_transfers_number_log_index",
    desc(ERC1155TokenTransfers.block_number),
    desc(ERC1155TokenTransfers.log_index),
)

Index(
    "erc1155_token_transfers_from_address_number_log_index_index",
    ERC1155TokenTransfers.from_address,
    desc(ERC1155TokenTransfers.block_number),
    desc(ERC1155TokenTransfers.log_index),
)
Index(
    "erc1155_token_transfers_to_address_number_log_index_index",
    ERC1155TokenTransfers.to_address,
    desc(ERC1155TokenTransfers.block_number),
    desc(ERC1155TokenTransfers.log_index),
)
Index(
    "erc1155_token_transfers_token_address_number_log_index_index",
    ERC1155TokenTransfers.token_address,
    desc(ERC1155TokenTransfers.block_number),
    desc(ERC1155TokenTransfers.log_index),
)
Index(
    "erc1155_token_transfers_token_address_id_index",
    ERC1155TokenTransfers.token_address,
    ERC1155TokenTransfers.token_id,
)
Index(
    "erc1155_token_transfers_token_address_from_index",
    ERC1155TokenTransfers.token_address,
    ERC1155TokenTransfers.from_address,
)
Index(
    "erc1155_token_transfers_token_address_to_index",
    ERC1155TokenTransfers.token_address,
    ERC1155TokenTransfers.to_address,
)