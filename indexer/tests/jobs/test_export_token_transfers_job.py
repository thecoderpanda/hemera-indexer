import pytest

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.token_transfer import ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.tests import LINEA_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[ERC721TokenTransfer, ERC1155TokenTransfer],
    )

    job_scheduler.run_jobs(
        start_block=7510938,
        end_block=7510938,
    )

    data_buff = job_scheduler.get_data_buff()
    job_scheduler.clear_data_buff()