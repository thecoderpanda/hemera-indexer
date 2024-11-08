import importlib
import itertools
import pkgutil
import random
import warnings
from typing import List, Optional, Union

from web3 import Web3

from common.utils.exception_control import RetriableError, decode_response_error
from indexer.domain import Domain

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def to_int_or_none(val):
    if isinstance(val, int):
        return val
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def to_float_or_none(val):
    if isinstance(val, float):
        return val
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        print("can't cast %s to float" % val)
        return val


def chunk_string(string, length):
    return (string[0 + i : length + i] for i in range(0, len(string), length))


# TODO: Implement fallback mechanism for provider uris instead of picking randomly
def pick_random_provider_uri(provider_uri):
    provider_uris = [uri.strip() for uri in provider_uri.split(",")]
    return random.choice(provider_uris)


def validate_range(range_start_incl, range_end_incl):
    if range_start_incl < 0 or range_end_incl < 0:
        raise ValueError("range_start and range_end must be greater or equal to 0")

    if range_end_incl < range_start_incl:
        raise ValueError("range_end must be greater or equal to range_start")


def rpc_response_batch_to_results(response):
    for response_item in response:
        yield rpc_response_to_result(response_item)


def rpc_response_to_result(response):
    result = response.get("result")
    if result is None:
        error_message = "result is None in response {}.".format(response)
        if response.get("error") is None:
            error_message = error_message + " Make sure Ethereum node is synced."
            # When nodes are behind a load balancer it makes sense to retry the request in hopes it will go to other,
            # synced node
            raise RetriableError(error_message)
        elif response.get("error") is not None:
            return decode_response_error(response.get("error"))
        else:
            return result
    return result


def zip_rpc_response(requests, responses, index="request_id"):
    response_dict = {}
    for response in responses:
        response_dict[response["id"]] = response

    for request in requests:
        request_id = request.get(index) if isinstance(request, dict) else getattr(request, index)
        if request_id in response_dict:
            yield request, response_dict[request_id]


def is_retriable_error(error_code):
    if error_code is None:
        return False

    if not isinstance(error_code, int):
        return False

    # https://www.jsonrpc.org/specification#error_object
    if error_code == -32603 or (-32000 >= error_code >= -32099):
        return True

    return False


def split_to_batches(start_incl, end_incl, batch_size):
    """start_incl and end_incl are inclusive, the returned batch ranges are also inclusive"""
    for batch_start in range(start_incl, end_incl + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_incl)
        yield batch_start, batch_end


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def check_classic_provider_uri(chain, provider_uri):
    if chain == "classic" and provider_uri == "https://mainnet.infura.io":
        warnings.warn("ETC Chain not supported on Infura.io. Using https://ethereumclassic.network instead")
        return "https://ethereumclassic.network"
    return provider_uri


def extract_pg_url_from_output(outputs: str) -> str:
    for output in outputs.split(","):
        if output.strip().startswith("postgresql"):
            return output

    return None


def merge_sort(sorted_col_a, sorted_col_b):
    merged = []
    a_index, a_len = 0, len(sorted_col_a)
    b_index, b_len = 0, len(sorted_col_b)

    while a_index < a_len and b_index < b_len:
        if sorted_col_a[a_index]["id"] < sorted_col_b[b_index]["id"]:
            merged.append(sorted_col_a[a_index])
            a_index += 1
        else:
            merged.append(sorted_col_b[b_index])
            b_index += 1

    merged.extend(sorted_col_a[a_index:])
    merged.extend(sorted_col_b[b_index:])

    return merged


def distinct_collections_by_group(collections: List[object], group_by: List[str], max_key: Union[str, None] = None):
    distinct = {}
    for item in collections:
        key = tuple(getattr(item, idx) for idx in group_by)

        if key not in distinct:
            distinct[key] = item
        else:
            if max_key is not None and getattr(distinct[key], max_key) < getattr(item, max_key):
                distinct[key] = item

    return [distinct[key] for key in distinct.keys()]


def format_block_id(block_id: Union[Optional[int], str]) -> str:
    return hex(block_id) if block_id and isinstance(block_id, int) else block_id


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()


def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
