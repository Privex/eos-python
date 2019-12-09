import math
import random
import sqlite3
import logging
from datetime import datetime, timedelta
from os.path import join, expanduser
from typing import Optional, List, Tuple, Union

from dateutil.tz import tzutc
from privex.helpers import empty, DictObject, empty_if

from privex.db import SqliteWrapper

from privex.eos.adapters import SqliteAdapter, BaseAdapter
from privex.eos.objects import convert_datetime, convert_bool_int, Node, WeightedNode

log = logging.getLogger(__name__)


def _row_node(id, url, network, enabled=1, fail_count=0, last_fail=None, created_at=None, updated_at=None, **kwargs):
    """
    Create a :class`.Node` from a database row, or specified arguments.
    """
    return Node(
        id=id, url=url, network=network, enabled=enabled, fail_count=fail_count, last_fail=last_fail,
        created_at=created_at, updated_at=updated_at
    )


def _node_to_row(node: Node):
    """
    Convert a :class:`.Node` object into a dictionary which is safe for passing to an insert row function.
    
    :param Node node: The :class:`.Node` to convert
    :return DictObject node_dict: The node, converted into a dictionary.
    """
    d = DictObject(url=node.url, network=node.network, enabled=node.enabled,
                   fail_count=node.fail_count, last_fail=node.last_fail)
    if node.id is not None:
        d['id'] = node.id
    
    return d


NODE_MANAGER_SCHEMA = [
    (
        'nodes',
        
        "CREATE TABLE nodes ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, network TEXT NOT NULL,"
        "   enabled INTEGER DEFAULT 1, last_success TIMESTAMP NULL, fail_count INTEGER DEFAULT 0,"
        "   last_fail TIMESTAMP NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "   UNIQUE(url, network) ON CONFLICT ABORT"
        ");",
     ),
    
    (
        'node_api',
        
        "CREATE TABLE node_api ("
        "   node_id INTEGER NOT NULL, api TEXT NOT NULL, endpoint TEXT NULL, "
        "   UNIQUE(node_id, api), FOREIGN KEY(node_id) REFERENCES nodes(id)"
        ");",
    ),
    
    (
        'node_failures',
        "CREATE TABLE node_failures ("
        "    node_id INTEGER NOT NULL, api TEXT NOT NULL, failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "    FOREIGN KEY(node_id) REFERENCES nodes(id)"
        ");",
    )
]

DEFAULT_ADAPTER = SqliteAdapter


def convert_nodes_weighted(total_fails: int, *nodes) -> List[WeightedNode]:
    """
    Convert :class:`.Node` objects into :class:`.WeightedNode` objects based on their failure counts
    compared to the ``total_fails`` argument.
    
    :param int total_fails: The total failures by **ALL** nodes on the node's network(s).
    :param Node nodes: A list of :class:`.Node` objects as positional args
    :return List[WeightedNode] weighted_nodes: A list of :class:`.WeightedNode`'s
    """
    weighted_nodes = []
    for n in nodes:
        if total_fails == 0:
            weight = 1
        elif n.fail_count in [None, 0]:
            weight = total_fails
        else:
            weight = math.ceil(total_fails / n.fail_count)
        weighted_nodes += [WeightedNode(node=n, weight=weight)]
    return weighted_nodes


class NodeManager:
    # DEFAULT_DB_FOLDER = expanduser('~/.privex_eos')
    # """If an absolute path isn't given, store the sqlite3 database file in this folder"""
    #
    # DEFAULT_DB_NAME = 'privex_eos.db'
    # """If no database is specified to :meth:`.__init__`, then use this (appended to :py:attr:`.DEFAULT_DB_FOLDER`)"""
    #
    # DEFAULT_DB = join(DEFAULT_DB_FOLDER, DEFAULT_DB_NAME)
    # """
    # Combined :py:attr:`.DEFAULT_DB_FOLDER` and :py:attr:`.DEFAULT_DB_NAME` used as default absolute path for
    # the sqlite3 database used for storing information about RPC nodes
    # """
    DEFAULT_NETWORK = 'eos'
    """If a network isn't specified to a method, use this network by default."""
    
    # SCHEMAS: List[Tuple[str, str]] = NODE_MANAGER_SCHEMA
    
    network: str
    """The current default network"""
    
    adapter: Union[BaseAdapter, SqliteAdapter]
    """The database adapter we're using to store and query nodes"""

    def __init__(self, network: str = DEFAULT_NETWORK, **kwargs):
        self.network = network
        self.adapter = kwargs.pop('adapter', None)
        if self.adapter is None:
            self.adapter = DEFAULT_ADAPTER()
        self.adapter.query_mode = kwargs.pop('query_mode', 'dict')
        # super().__init__(db=db, query_mode=self.query_mode, **kwargs)

    def builder(self, table): return self.adapter.builder(table)
    
    @property
    def node_builder(self): return self.builder('nodes')

    @property
    def conn(self): return self.adapter.conn

    @property
    def cursor(self): return self.adapter.cursor
    
    def fail_node(self, node: Union[Node, int, str]) -> Node:
        """
        Mark a node as failed to reduce the chance of it being selected, and prevents it being selected
        in :attr:`.weighted_node` for at least 5 seconds.
        
        :param Node node: A :class:`.Node` object to mark as failed
        :param int node: An integer node ID to mark as failed
        :param str node: An node URL to mark as failed
        :return Node node: A freshly loaded :class:`.Node` object with the updated fail info.
        """
        if type(node) is str:
            node_id = self.node_by_url(node).id
        else:
            node_id = node if type(node) is int else node.id
        self.adapter.action("UPDATE nodes SET fail_count = fail_count + 1, last_fail = ? "
                            "WHERE id = ?;", [datetime.utcnow(), node_id])
        return self.node_by_id(node_id)
    
    @property
    def node_count(self) -> int:
        return int(self.node_builder.select('COUNT(*) as node_count')[0]['node_count'])
    
    def insert_node(self, node: Node):
        """
        Insert a :class:`.Node` object into the database
        :param Node node: The node object to insert
        """
        return self.insert(
            **_node_to_row(node)
            # url=node.url, network=node.network, enabled=node.enabled,
            # fail_count=node.fail_count, last_fail=node.last_fail
        )

    def insert(self, url, network=None, enabled=1, fail_count=0, last_fail=None, **kwargs):
        """
        Insert a node into the database using the arguments specified to this function.
        
        :param str url: The URL for the RPC node
        :param str network: Defaults to :attr:`.DEFAULT_NETWORK` if not specified
        :param int enabled: Either 1 (enabled) or 0 (disabled)
        :param int fail_count: The amount of times this node has responded with a non-200 status.
        :param str last_fail: The date/time when this node last failed
        :param kwargs: Any additional columns to insert.
        """
        data = dict(
            url=url, network=empty_if(network, self.network), enabled=convert_bool_int(enabled),
            fail_count=int(fail_count), last_fail=convert_datetime(last_fail), updated_at=datetime.utcnow()
        )
        return self.adapter.insert('nodes', **data, **kwargs)

    def bulk_insert(self, *nodes: Union[dict, Node], ignore_conflict=False) -> int:
        """
        
        Example::
            
            >>> nm = NodeManager()
            >>> nm.bulk_insert(dict(url='http://example.com'), dict(url='http://example.org'))
            2
        
        :param dict nodes: One or more nodes to insert, as dictionaries
        :param bool ignore_conflict: (Default: ``False``) - If set to ``True``, then exceptions caused due to
                                     rows already existing will be ignored, instead of causing a rollback.
        :return int rows_affected:   Number of rows inserted
        """
        c = self.conn.cursor()
        rows_affected = 0
        self.adapter.begin_transaction(c)
        n = None
        try:
            for n in nodes:
                if isinstance(n, Node):
                    n = _node_to_row(n)
                try:
                    res = self.insert(_cursor=c, **n)
                    log.debug('Called _insert with kwargs: %s', n)
                    log.debug('Result: %s', res)
                    rows_affected += res.rowcount
                except sqlite3.IntegrityError as e:
                    log.error("Integrity error while inserting node: %s - Type: %s // Msg: %s", n, type(e), str(e))
                    if ignore_conflict:
                        log.warning("ignore_conflicts is True. Simply skipping this node...")
                        continue
                    raise e
            self.adapter.commit_transaction(c)
        except (sqlite3.Error, Exception, BaseException) as e:
            log.exception("Exception while inserting node: %s", n)
            self.adapter.rollback_transaction(c)
            c.close()
            raise e
            
        return rows_affected
    
    def get_nodes(self, *networks, filter_fail=False) -> List[Node]:
        """
        Get a list of :class:`.Node` objects.
        
        :param str networks: Restrict the node list to nodes on these networks
        :param bool filter_fail: If set to ``True``, nodes which have their ``last_fail`` within the past
                                 5 seconds will be removed from the returned node list.
        :return List[Node] nodes: A list of :class:`.Node` objects.
        """
        # c = self.conn.cursor()
        nodes = []
        if len(networks) == 0:
            query = self.node_builder.where('network', self.network)
        else:
            query = self.node_builder.where('network', networks, 'IN', '(?)')
            # for r in self.fetch("SELECT * FROM nodes WHERE network = ?", [self.network]):
        for r in query:
            n = _row_node(**r)
            
            if filter_fail and n.last_fail is not None:
                n.last_fail = n.last_fail.replace(tzinfo=None)
                secs_ago = datetime.utcnow() - timedelta(seconds=5)
                secs_ago.replace(tzinfo=None)
                if n.last_fail > secs_ago:
                    continue
            nodes += [n]
        return nodes
        
        # # for r in self.fetch("SELECT * FROM nodes WHERE network IN (?)", [list(networks)]):
        # for r in self.node_builder.where('network', self.network, 'IN', '(?)'):
        #     n = _row_node(**r)
        #
        #     if filter_fail and n.last_fail is not None:
        #         if n.last_fail > (datetime.utcnow() - timedelta(seconds=5)):
        #             continue
        #     nodes += [n]
        
        # return nodes

    def get_weighted_nodes(self, *networks, filter_fail=False) -> List[WeightedNode]:
        nb = self.node_builder
        total_fails = nb.select('SUM(fail_count) as total_fails')[0]['total_fails']
        total_fails = int(total_fails)
        
        nodes = self.get_nodes(*networks, filter_fail=filter_fail)
        # weighted_nodes = []
        # for n in nodes:
        #     weight = math.ceil(total_fails / (n.fail_count + 1))
        #     weighted_nodes += [WeightedNode(node=n, weight=weight)]
        weighted_nodes = convert_nodes_weighted(total_fails, *nodes)
        return weighted_nodes

    @property
    def weighted_node(self) -> Optional[Node]:
        weight_nodes = self.weight_nodes()
        if len(weight_nodes) == 0:
            return None
        return random.choice(weight_nodes)
    
    def weight_nodes(self, nodes: List[WeightedNode] = None) -> List[Node]:
        
        if nodes is None:
            nodes = self.get_weighted_nodes(filter_fail=True)
        mixed_nodes = []
        for n in nodes:
            for _ in range(n.weight):
                mixed_nodes += [n.node]
        return mixed_nodes

    def node_by_id(self, id: int) -> Optional[Node]:
        # c = self.conn.cursor()
        # c.execute("SELECT * FROM nodes WHERE id = ?", [int(id)])
        # row = c.fetchone()
        row = self.node_builder.where('id', int(id)).fetch()
        # row = self.fetchone("SELECT * FROM nodes WHERE id = ?", [int(id)])
        return None if row is None else _row_node(**row)

    def node_by_url(self, url: str, network: str = None) -> Optional[Node]:
        network = self.network if empty(network) else network
        row = self.node_builder.where('url', url).where('network', network).fetch()
        # row = self.fetchone("SELECT * FROM nodes WHERE url = ? AND network = ?", [url, network])
        return None if row is None else _row_node(**row)

    def __enter__(self):
        return self
        # self._conn = sqlite3.connect(self.db)
        # return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.adapter.close_cursor()

