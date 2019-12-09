from datetime import datetime
from typing import Union, List, Optional

import attr
from dateutil.parser import parse
from privex.coin_handlers.base.objects import AttribDictable
from privex.helpers import empty, is_true, convert_datetime, DictObject


def attr_dict(cls: type, data: dict):
    """
    Removes keys from the passed dict ``data`` which don't exist on ``cls`` (thus would get rejected as kwargs),
    then create and return an instance of ``cls``, passing the filtered data as keyword args.

    Ensures that any keys in your dictionary which don't exist on ``cls`` are automatically filtered out, instead
    of causing an error due to unexpected keyword arguments.

    Example::

        >>> data = dict(timestamp="2019-01-01Z00:00", producer='eosio', block_num=1234, example='hello')
        >>> my_block = attr_dict(EOSBlock, data)


    :param cls:
    :param data:
    :return:
    """
    if hasattr(cls, '__attrs_attrs__'):
        cls_keys = [atr.name for atr in cls.__attrs_attrs__]
    else:
        cls_keys = [k for k in cls.__dict__.keys() if k[0] != '_']
    
    clean_data = {x: y for x, y in data.items() if x in cls_keys}
    return cls(**clean_data)


@attr.s
class EOSTransaction(AttribDictable):
    status = attr.ib(type=str)
    cpu_usage_us = attr.ib(type=int, default=0)
    net_usage_words = attr.ib(type=int, default=0)
    trx = attr.ib(type=Union[dict, str], default=None)
    """
    Contents of ``trx``::

        dict_keys([
            id:str, signatures:list, compression:str, packed_context_free_data:str, context_free_data:list,
            packed_trx:str, transaction:dict
        ])

    """
    
    id = attr.ib(type=str)
    signatures = attr.ib(type=list)
    compression = attr.ib(type=str)
    context_free_data = attr.ib(type=list)
    packed_trx = attr.ib(type=str)
    transaction = attr.ib(type=Union[dict, str])
    """
    Contents of ``trx['transaction']``::

        dict_keys([
            expiration:str, ref_block_num:int, ref_block_prefix:int, max_net_usage_words:int, max_cpu_usage_ms:int,
            delay_sec:int, context_free_actions:list, actions:List[dict], transaction_extensions:list
        ])

    Contents of a ``trx['transaction']['actions']`` dict::

        dict_keys([account:str, name:str, authorization:List[dict], data:dict, hex_data])

    """
    
    @id.default
    def _id_default(self):
        if type(self.trx) is str:
            return self.trx
        if type(self.trx) is dict:
            return self.trx['id']
        return None
    
    @signatures.default
    def _signatures_default(self):
        return self.trx['signatures'] if type(self.trx) is dict else []
    
    @compression.default
    def _compression_default(self):
        return self.trx['compression'] if type(self.trx) is dict else 'none'
    
    @context_free_data.default
    def _context_free_data_default(self):
        return self.trx['context_free_data'] if type(self.trx) is dict else []
    
    @packed_trx.default
    def _packed_trx_default(self):
        return self.trx['packed_trx'] if type(self.trx) is dict else None
    
    @transaction.default
    def _transaction_default(self):
        return self.trx['transaction'] if type(self.trx) is dict else None
    
    @staticmethod
    def from_dict(data: dict):
        if isinstance(data, EOSTransaction):
            return data
        return attr_dict(EOSTransaction, data)
    
    @staticmethod
    def from_list(data: List[dict]) -> list:
        if len(data) == 0:
            return []
        if isinstance(data[0], EOSTransaction):
            return data
        
        return [attr_dict(EOSTransaction, d) for d in data]


@attr.s
class EOSBlock(AttribDictable):
    timestamp = attr.ib(type=str)
    producer = attr.ib(type=str)
    block_num = attr.ib(type=int)
    ref_block_prefix = attr.ib(type=int)
    
    confirmed = attr.ib(type=int, default=0)
    previous = attr.ib(type=str, default=None)
    transaction_mroot = attr.ib(type=str, default=None)
    action_mroot = attr.ib(type=str, default=None)
    id = attr.ib(type=str, default=None)
    new_producers = attr.ib(default=None)
    header_extensions = attr.ib(type=list, factory=list)
    producer_signature = attr.ib(type=str, default=None)
    transactions = attr.ib(type=List[EOSTransaction], factory=list, converter=EOSTransaction.from_list)
    block_extensions = attr.ib(type=list, factory=list)
    schedule_version = attr.ib(type=int, default=None)
    
    @staticmethod
    def from_dict(data: dict):
        return attr_dict(EOSBlock, data)
    
    @staticmethod
    def from_list(data: List[dict]) -> list:
        return [attr_dict(EOSBlock, d) for d in data]


@attr.s
class EOSAccount(AttribDictable):
    account_name = attr.ib(type=str)
    last_code_update = attr.ib(type=str, converter=convert_datetime)
    created = attr.ib(type=str, converter=convert_datetime)
    core_liquid_balance = attr.ib(type=str)
    ram_quota = attr.ib(type=int)
    net_weight = attr.ib(type=int)
    cpu_weight = attr.ib(type=int)
    ram_usage = attr.ib(type=int)
    self_delegated_bandwidth = attr.ib(type=dict, default=None)
    refund_request = attr.ib(default=None)
    rex_info = attr.ib(default=None)
    voter_info = attr.ib(type=DictObject, factory=DictObject, converter=DictObject)
    total_resources = attr.ib(type=DictObject, factory=DictObject, converter=DictObject)
    permissions = attr.ib(type=list, factory=list)
    net_limit = attr.ib(type=DictObject, factory=DictObject, converter=DictObject)
    cpu_limit = attr.ib(type=DictObject, factory=DictObject, converter=DictObject)
    privileged = attr.ib(type=bool, default=False)
    head_block_num = attr.ib(type=int, default=0)
    head_block_time = attr.ib(type=str, default=None)

    @staticmethod
    def from_dict(data: dict):
        return attr_dict(EOSAccount, data)

    @staticmethod
    def from_list(data: List[dict]) -> list:
        return [attr_dict(EOSAccount, d) for d in data]

# def convert_datetime(d):
#     if type(d) in [str, int]:
#         d = parse(d)
#     if empty(d): return None
#     if not isinstance(d, datetime):
#         raise ValueError('Timestamp must be either a datetime object, or an ISO8601 string...')
#     return d


def convert_bool_int(d, if_empty=True) -> int:
    if type(d) is int: return 1 if d >= 1 else 0
    if empty(d): return 1 if if_empty else 0
    return 1 if is_true(d) else 0


def convert_int_bool(d, if_empty=True) -> bool:
    if empty(d): return if_empty
    return is_true(d)


@attr.s
class Node(AttribDictable):
    id = attr.ib(type=Optional[int])
    url = attr.ib(type=str)
    network = attr.ib(type=str, default=None)
    enabled = attr.ib(type=Union[bool, int], default=True, converter=convert_int_bool)
    fail_count = attr.ib(type=int, default=0)
    last_success = attr.ib(type=datetime, default=None, converter=convert_datetime)
    last_fail = attr.ib(type=datetime, default=None, converter=convert_datetime)
    created_at = attr.ib(type=datetime, default=None, converter=convert_datetime)
    updated_at = attr.ib(type=datetime, default=None, converter=convert_datetime)


@attr.s
class WeightedNode(AttribDictable):
    node = attr.ib(type=Node)
    weight = attr.ib(type=int, default=0)

