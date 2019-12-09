import math

from privex.eos.node import _node_to_row, convert_nodes_weighted
from tests.base import BaseEOSTest
import logging

log = logging.getLogger(__name__)


class TestNodeManager(BaseEOSTest):
    def test_basic_insert(self):
        n = self.example_nodes[0]
        self.nm.insert(
            url=n.url, network=n.network, enabled=n.enabled
        )
        
        res = self.nm.node_by_url(url=n.url, network=n.network)

        self._compare_node(n, res)

    def test_node_object_insert(self):
        n = self.example_nodes[0]
        self.nm.insert_node(n)

        res = self.nm.node_by_url(url=n.url, network=n.network)

        self._compare_node(n, res)

    def test_bulk_insert(self):
        self.nm.bulk_insert(*self.node_dicts)
        
        for n in self.example_nodes:
            res = self.nm.node_by_url(url=n.url, network=n.network)

            self._compare_node(n, res)

    @staticmethod
    def _node_eq(first, second):
        url_eq = first['url'] == second['url']
        network_eq = first['network'] == second['network']
        enabled_eq = first['enabled'] == second['enabled']
        return url_eq and network_eq and enabled_eq

    def _compare_node(self, first, second):
        self.assertEqual(first.url, second.url)
        self.assertEqual(first.network, second.network)
        self.assertEqual(first.enabled, second.enabled)

    def test_get_nodes(self):
        self.nm.bulk_insert(*self.node_dicts)
        
        nodes = self.nm.get_nodes()
        
        for n in self.node_dicts:
            found = False
            for k in nodes:
                if self._node_eq(n, k):
                    found = True
            self.assertTrue(found, msg=f'Node "{n["url"]}" in node list: {nodes}')

    def test_fail_node(self):
        n = self.example_nodes[0]
        self.nm.insert_node(n)
        n = self.nm.node_by_url(n.url)
        new_n = self.nm.fail_node(n)
        self.assertEqual(new_n.fail_count, n.fail_count + 1)
        new_n = self.nm.fail_node(n)
        self.assertEqual(new_n.fail_count, n.fail_count + 2)
    
    def test_weighted_nodes(self):
        self.nm.bulk_insert(*self.node_dicts)
        nodes = self.nm.get_nodes()
        
        nodes[0].fail_count = 5
        nodes[1].fail_count = 10
        nodes[2].fail_count = 0
        total_fails = 16
        log.warning("Node 0: %s", nodes[0].url)
        log.warning("Node 1: %s", nodes[1].url)
        log.warning("Node 2: %s", nodes[2].url)

        _weighted_nodes = convert_nodes_weighted(total_fails, nodes[0], nodes[1], nodes[2])
        weighted_nodes = self.nm.weight_nodes(_weighted_nodes)
        counts = {}
        for n in weighted_nodes:
            if n.url not in counts: counts[n.url] = 0
            counts[n.url] += 1
        
        self.assertEqual(counts[nodes[0].url], math.ceil(total_fails / nodes[0].fail_count))
        self.assertEqual(counts[nodes[1].url], math.ceil(total_fails / nodes[1].fail_count))
        self.assertEqual(counts[nodes[2].url], math.ceil(total_fails / 1))
        log.warning("Node counts: %s", counts)
