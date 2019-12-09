"""
Async EOS API client allowing for high speed block importing

**Copyright**::

    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Privex EOS Python API                      |
    |        License: X11 / MIT                         |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

"""
import asyncio
import time
import random
from collections import OrderedDict
from typing import Union, Optional, Dict, List
import httpx
from privex.helpers import DictObject
from privex.helpers.asyncx import run_sync

from privex.eos.node import NodeManager
from privex.eos.objects import EOSBlock, Node, EOSAccount
import logging

log = logging.getLogger(__name__)


class Api:
    """
    AsyncIO API library for EOS - by Privex Inc. (https://www.privex.io)
    
    **Usage**
    
    Create instance::
        
        >>> from privex.eos import Api
        >>> eos = Api()
    
    Add additional RPC nodes (if needed)::
        
        >>> from privex.eos import Node
        >>> example_node = Node(url='http://example.com', network='eos', enabled=1, id=None)
        >>> eos.node_manager.insert_node(example_node)
    
    Reset the node database::
        
        >>> eos.node_manager.adapter.recreate_schemas()
        >>> eos = Api()
    
    Get a block::
        
        >>> block = await eos.get_block(94000000)
        >>> block.block_num
        94000000
        >>> block.id
        '059a5380852aef1ee27a0cd75953f76bb334ad402b4e0360dada1a17ee486357'
        >>> block.producer
        'eoshuobipool'
    
    
    
    **Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Privex EOS Python API                      |
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |                                                   |
        +===================================================+
    
    
    """
    DEFAULT_NODES = [
        Node(url='https://eos.greymass.com', network='eos', enabled=1, id=None),
        Node(url='https://api.eosdetroit.io', network='eos', enabled=1, id=None),
        Node(url='https://api.eosnewyork.io', network='eos', enabled=1, id=None),
        # Node(url='https://api1.eosdublin.io', network='eos', enabled=1, id=None),
        # Node(url='https://eos.saltblock.io', network='eos', enabled=1, id=None),
    ]
    # url: str
    api_root_chain = '/v1/chain'
    api_root_node = '/v1/node'
    api_root_producer = '/v1/producer'
    endpoints = {
        'get_account':          f'{api_root_chain}/get_account',
        'get_block':            f'{api_root_chain}/get_block',
        'get_info':             f'{api_root_chain}/get_info',
        'get_currency_balance': f'{api_root_chain}/get_currency_balance',
        'get_currency_stats':   f'{api_root_chain}/get_currency_stats',
        'get_producers':        f'{api_root_chain}/get_producers',
        'get_table_by_scope':   f'{api_root_chain}/get_table_by_scope',
        'get_table_rows':       f'{api_root_chain}/get_table_rows',
        'get_supported_apis':   f'{api_root_node}/get_supported_apis',
    }
    
    client: httpx.Client
    
    # def __init__(self, url="https://eos.greymass.com", **kwargs):
    def __init__(self, node_manager=None, **kwargs):
        if node_manager is None:
            node_manager = NodeManager(network='eos')
        self.node_manager = node_manager
        if node_manager.node_count == 0:
            log.info("Node manager database is empty. Adding DEFAULT_NODES.")
            node_manager.bulk_insert(*self.DEFAULT_NODES)
        
        # self.current_node = node_manager.weighted_node
        while node_manager.weighted_node is None:
            log.info("[__init__] current_node is None. Waiting a few seconds for last_fail's to get older.")
            time.sleep(3)
            # self.current_node = node_manager.weighted_node
        self.client = httpx.Client(timeout=30)
        httpx.TimeoutConfig(30)
        
        # self.url = self.current_node.url.strip().strip('/')
        # self.client = client = httpx.client.Client()
        # client.headers['Content-Type'] = 'application/json'
        self.max_retries = int(kwargs.pop('max_retries', 10))
        self.retry_wait = float(kwargs.pop('retry_wait', 2.0))
    
    @property
    def url(self) -> Optional[str]:
        n = self.node_manager.weighted_node
        if n is None: return None
        return n.url
    
    async def get_block(self, number: int) -> EOSBlock:
        """
        Get the contents of the EOS block number ``number`` - returned as a dictionary (see detailed return info
        at bottom of this method's docs).

        Example::

            >>> a = Api()
            >>> b = await a.get_block(1234)
            >>> b['producer']
            'eosio'
            >>> b['id']
            '000004d25627320e2f442b62ac39735caf0dbc5c0c5c8c0ac0ba735c17a022e7'


        :param number:
        :return:

        Returned dictionary::

             dict_keys([
                timestamp:str, producer:str, confirmed:int, previous:str, transaction_mroot:str, action_mroot:str,
                id:str, new_producers, header_extensions:list, producer_signature:str, transactions:List[dict],
                block_extensions:list, block_num:int, ref_block_prefix:int, schedule_version:int
             ])

        **Content of transactions list**::

        First layer dict::

            dict_keys(['status', 'cpu_usage_us', 'net_usage_words', 'trx'])

        Contents of ``trx``::

            dict_keys([
                id:str, signatures:list, compression:str, packed_context_free_data:str, context_free_data:list,
                packed_trx:str, transaction:dict
            ])

        Contents of ``trx['transaction']``::

            dict_keys([
                expiration:str, ref_block_num:int, ref_block_prefix:int, max_net_usage_words:int, max_cpu_usage_ms:int,
                delay_sec:int, context_free_actions:list, actions:List[dict], transaction_extensions:list
            ])

        Contents of a ``trx['transaction']['actions']`` dict::

            dict_keys([account:str, name:str, authorization:List[dict], data:dict, hex_data])

         * ``account`` - The account / contract which created the action

         * ``name`` - The type of action occurring, e.g. ``newaccount``, ``buyrambytes`` or ``transfer``

         * ``data`` - Usually a dictionary containing metadata about the action, such as how many tokens were
           transferred, how much of a token was staked, who the TX is *actually* from/to etc.

        """
        b = await self._call(self.endpoints['get_block'], block_num_or_id=number)
        
        return EOSBlock.from_dict(b)

    async def get_block_range(self, start: int, end: int) -> Dict[int, EOSBlock]:
        coros = {}
        for i in range(start, end + 1):
            coros[i] = self.get_block(i)
        
        results = await asyncio.gather(*coros.values())
        return OrderedDict(zip(coros.keys(), results))
    
    async def get_info(self) -> dict:
        return await self._call(self.endpoints['get_info'])

    async def get_account(self, account_name) -> EOSAccount:
        a = await self._call(self.endpoints['get_account'], account_name=account_name)
        return EOSAccount.from_dict(a)

    async def get_currency_balance(self, code: str, account: str, symbol: str) -> List[str]:
        return await self._call(self.endpoints['get_currency_balance'], code=code, account=account, symbol=symbol)

    async def _call(self, _endpoint: str, *args, **kwargs) -> Union[dict, list]:
        """
        Internal function used for making an async EOS RPC call.

        If positional arguments are specified, the JSON POST payload will be a list composed of positional arguments
        (specified after _endpoint).
        If no positional args are specified, then keyword arguments will be used - the JSON POST payload will be a
        dictionary composed of the kwargs.

        Example usage - keyword args are sent as a JSON dict::

            >>> self._call('/v1/chain/get_block', block_num_or_id=12345)

        Example usage - positional args are sent as a JSON list/array::

            >>> self._call('/v1/chain/push_transactions', {"expiration": 1234}, {"expiration": 3456})


        :param str _endpoint: The URL endpoint to call, e.g. ``/v1/chain/get_block``
        :param args: Positional arguments will be converted into a list and sent as the JSON POST body.
        :param kwargs: Keyword arguments will be converted into a dict and sent as the JSON POST body.
        :return dict|list result: The response returned from the RPC call.
        """
        retry_count = kwargs.pop('_retry_count', 0)
        raise_status = kwargs.pop('_raise_status', True)
        _endpoint = '/' + _endpoint.strip('/')
        body = list(args) if len(args) > 0 else dict(kwargs)
        # async with httpx.AsyncClient() as client:
        node_url = self.url
        while node_url is None:
            log.warning("All nodes broken. Waiting for functional node...")
            await asyncio.sleep(random.random() * 4)
            node_url = self.url
        url = node_url.strip().strip('/') + _endpoint
        
        # client.headers['Content-Type'] = 'application/json'
        try:
            await asyncio.sleep(random.random() * 3)
            r = await self.client.post(url, json=body, headers={'Content-Type': 'application/json'})
            if raise_status:
                r.raise_for_status()
            res = r.json()
        except (BaseException, Exception) as e:
            log.warning("Exception '%s' while calling %s with body %s\n\tMessage: %s",
                        type(e), url, body, str(e))
            await self._fail_node(node_url)
            if retry_count >= self.max_retries:
                log.exception("[RETRIES EXCEEDED] Exception '%s' while calling %s with body %s\n\tMessage: %s",
                              type(e), url, body, str(e))
                raise e
            retry_count += 1
            log.warning("[Retry %d / %d] Retrying call.", retry_count, self.max_retries)
            await asyncio.sleep(self.retry_wait)
            res = await self._call(_endpoint, *args, **kwargs, _retry_count=retry_count)
        
        if isinstance(res, dict):
            return DictObject(res)
        
        return res

    async def _fail_node(self, node):
        """Increment the fail_count for the current node and get a new weighted RPC node"""
        # node = self.current_node if node is None else node
        n = self.node_manager.fail_node(node)
        log.warning("Incremented fail_count to %s for node %s", n.fail_count, n.url)
        # new_node = self.node_manager.weighted_node
        while self.node_manager.weighted_node is None:
            log.info("[_fail_node] All nodes broken. Waiting 5 seconds for last_fail's to get older.")
            await asyncio.sleep(5)
            # new_node = self.node_manager.weighted_node
        # self.current_node = new_node
        # log.warning("Updated current node to: %s", self.current_node.url)

    def sync_call(self, _endpoint: str, *args, **kwargs) -> Union[DictObject, dict, list]:
        """
        This method is primarily intended for debugging, and is not recommended for actual use in code.

        It uses privex-helpers' :func:`.run_sync` to run :meth:`._call` synchronously, allowing for debugging
        this class via the standard Python REPL which doesn't allow for ``await`` or ``async with`` etc.

        :param str _endpoint: The URL endpoint to call, e.g. ``/v1/chain/get_block``
        :param args: Positional arguments will be converted into a list and sent as the JSON POST body.
        :param kwargs: Keyword arguments will be converted into a dict and sent as the JSON POST body.
        :return dict|list result: The response returned from the RPC call.
        """
        return run_sync(self._call, _endpoint, *args, **kwargs)

    async def get_supported_apis(self) -> List[str]:
        apis = await self._call(self.endpoints['get_supported_apis'])
        return apis['apis']
    
    def __getattr__(self, name):
        """
        Methods that haven't yet been defined are simply passed off to :meth:`._call` with the positional and kwargs.

        This means ``rpc.get_abi(account_name='john')`` is equivalent to ``rpc._call('get_abi', account_name='john')``

        :param name: Name of the attribute requested
        :return: Dict or List from call result
        """
        
        async def c(*args, **kwargs):
            
            endpoint = self.endpoints.get(name)
            if endpoint is not None:
                return await self._call(endpoint, *args, **kwargs)
            apis = await self.get_supported_apis()
            for a in apis:
                if name in a:
                    return await self._call(a, *args, **kwargs)
        
        return c
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
