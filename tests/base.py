from typing import NamedTuple, Type
from unittest import TestCase

from privex.eos import NodeManager, Node
# from privex.helpers import dictable_namedtuple

# Node: Type[NamedTuple] = dictable_namedtuple('Node', 'url network enabled')
from privex.eos.adapters import SqliteAdapter
from privex.eos.node import _node_to_row


class BaseEOSTest(TestCase):
    example_nodes = [
        Node(url='https://eos.greymass.com', network='eos', enabled=1, id=None),
        Node(url='https://api.eosdetroit.io', network='eos', enabled=1, id=None),
        Node(url='https://api.eosnewyork.io', network='eos', enabled=1, id=None),
    ]
    node_dicts = [_node_to_row(n) for n in example_nodes]
    
    @classmethod
    def setUpClass(cls) -> None:
        adapter = SqliteAdapter(db=':memory:')
        cls.nm = NodeManager(adapter=adapter)
    
    def setUp(self) -> None:
        self.nm.adapter.recreate_schemas()
    
    def tearDown(self) -> None:
        self.nm.adapter.drop_schemas()

