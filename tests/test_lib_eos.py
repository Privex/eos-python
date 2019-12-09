from collections import OrderedDict
from decimal import Decimal

import pytest
from privex.helpers import DictObject, empty

from privex.eos.lib import Api, EOSBlock, Node
from privex.eos.node import NodeManager, DEFAULT_ADAPTER
from privex.eos.objects import EOSAccount

EXAMPLE_BLOCK_NUM = 94000000
EXAMPLE_BLOCK_DATA = DictObject(
    timestamp='2019-12-08T23:19:55.000',
    producer='eoshuobipool',
    block_num=94000000,
    ref_block_prefix=3607919330,
    previous='059a537fa917845911fc05e8f6b305e90a837eaba935ae65617125291cb307b4',
    id='059a5380852aef1ee27a0cd75953f76bb334ad402b4e0360dada1a17ee486357',
    producer_signature='SIG_K1_K9EoSbEcLaeXgJWwwQTiL9k4RsQW2DwS7nng77v6y8nZ8gJYC6qBknumsnq'
                       'Q3vXChsK2KpkgzKVcPEC8YgT8RUxWrHJatP',
    _total_txs=13
)

RANGE_START = EXAMPLE_BLOCK_NUM
RANGE_END = RANGE_START + 20


@pytest.fixture()
async def eos_api():
    Api().node_manager.adapter.recreate_schemas()
    eos = Api()
    yield eos


@pytest.mark.asyncio
async def test_eos_getinfo(eos_api: Api):
    info = await eos_api.get_info()
    assert isinstance(info, dict)
    assert isinstance(info, DictObject)
    assert info['chain_id'] == 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906'
    assert type(info.head_block_num) is int
    assert type(info.last_irreversible_block_num) is int
    assert info.head_block_num > 94000000


@pytest.mark.asyncio
async def test_eos_get_account(eos_api: Api):
    acc = await eos_api.get_account('someguy12333')
    assert isinstance(acc, EOSAccount)
    assert acc.account_name == 'someguy12333'
    assert not acc.privileged
    assert not empty(acc.created)
    assert not empty(acc.last_code_update)
    assert 'EOS' in acc.core_liquid_balance


@pytest.mark.asyncio
async def test_eos_get_currency_balance(eos_api: Api):
    bal = await eos_api.get_currency_balance('eosio.token', 'someguy12333', 'EOS')
    bal_amount, bal_currency = bal[0].split(' ')
    bal_amount = Decimal(bal_amount)
    assert bal_currency == 'EOS'
    assert bal_amount > 0
    
    bal = await eos_api.get_currency_balance('sandiegocoin', 'someguy12333', 'SAND')
    bal_amount, bal_currency = bal[0].split(' ')
    bal_amount = Decimal(bal_amount)
    assert bal_currency == 'SAND'
    assert bal_amount > 0


def test_eos_sync_call(eos_api: Api):
    block = eos_api.sync_call(eos_api.endpoints['get_block'], block_num_or_id=EXAMPLE_BLOCK_NUM)
    assert block.block_num == EXAMPLE_BLOCK_NUM
    assert block.id == EXAMPLE_BLOCK_DATA.id


@pytest.mark.asyncio
async def test_eos_getattribute(eos_api: Api):
    acc = await eos_api.__getattribute__('get_account')(account_name='someguy12333')
    assert acc.account_name == 'someguy12333'
    assert not empty(acc.created)
    assert not empty(acc.last_code_update)
    assert 'EOS' in acc.core_liquid_balance


@pytest.mark.asyncio
async def test_eos_get_supported_apis(eos_api: Api):
    apis = await eos_api.get_supported_apis()
    assert isinstance(apis, list)
    assert '/v1/chain/get_block' in apis
    assert '/v1/chain/get_info' in apis


@pytest.mark.asyncio
async def test_eos_getblock(eos_api: Api):
    block = await eos_api.get_block(EXAMPLE_BLOCK_NUM)
    assert isinstance(block, EOSBlock)
    assert block.block_num == EXAMPLE_BLOCK_DATA.block_num
    assert block.producer == EXAMPLE_BLOCK_DATA.producer
    assert block.timestamp == EXAMPLE_BLOCK_DATA.timestamp
    assert block.id == EXAMPLE_BLOCK_DATA.id
    assert len(block.transactions) == EXAMPLE_BLOCK_DATA._total_txs


@pytest.mark.asyncio
async def test_eos_getblock_range(eos_api: Api):
    blocks = await eos_api.get_block_range(start=RANGE_START, end=RANGE_END)
    assert isinstance(blocks, dict)
    assert isinstance(blocks, OrderedDict)
    assert len(blocks.keys()) == ((RANGE_END - RANGE_START) + 1)
    assert RANGE_START in blocks
    assert RANGE_END in blocks
    i = RANGE_START
    for block_num, block in blocks.items():
        assert block_num == i
        assert block.block_num == block_num
        assert not empty(block.id)
        assert not empty(block.producer)
        assert not empty(block.timestamp)
        i += 1


@pytest.mark.asyncio
async def test_eos_node_failover(eos_api: Api):
    real_node = eos_api.DEFAULT_NODES[0]
    fake_node = Node(url='http://example.com', network='eos', enabled=1, id=None)
    
    adapter = DEFAULT_ADAPTER(memory_persist=True)
    # Keepalive connection to avoid the memory persistent DB getting deleted
    _conn = adapter.make_connection(*adapter.connector_args, **adapter.connector_kwargs)
    # Create a NodeManager and add our real node, and fake node
    nm = NodeManager(adapter=adapter)
    nm.insert_node(real_node)
    nm.insert_node(fake_node)
    # Verify that our real node and fake node are present in the DB
    nodes = nm.get_nodes()
    assert nodes[0].url == real_node.url
    assert nodes[1].url == fake_node.url
    
    # Create an EOS API instance using our node manager
    eos = Api(node_manager=nm)
    assert eos.node_manager is nm
    
    # Make several calls to make sure that the fake node is tried, and fails
    for _ in range(5):
        await eos.get_info()
        await eos.get_block(EXAMPLE_BLOCK_NUM)
    # The fake_node should've failed enough by now that the current node URL should be
    # the real working node URL.
    assert eos.url == real_node.url
