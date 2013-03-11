import os
from unittest import TestCase


class TestCluster(TestCase):

    def setUp(self):
        self._cluster = None

    def tearDown(self):
        if self._cluster:
            self._cluster.terminate()

    def _make_one(self, **kw):
        from pyelastictest import cluster
        es_path = cluster.get_es_path()
        self._cluster = cluster.Cluster(es_path, **kw)
        return self._cluster

    def test_cluster_init(self):
        cluster = self._make_one()
        self.assertEqual(cluster.nodes, [])

    def test_cluster_init_ports(self):
        cluster = self._make_one(size=2, ports=[(9201, 9202), (9203, 9204)])
        self.assertEqual(cluster.ports, [9201, 9203])
        self.assertEqual(cluster.transport_ports, [9202, 9204])

    def test_cluster_init_size_ports_mismatch(self):
        self.assertRaises(ValueError,
            self._make_one, size=2, ports=[(9201, 9202)])

    def test_cluster_start(self):
        cluster = self._make_one()
        cluster.start()
        self.assertTrue(cluster.client is not None)
        self.assertEqual(cluster.client.health()['number_of_nodes'], 1)

    def test_cluster_start_twice(self):
        cluster = self._make_one()
        cluster.start()
        cluster.start()

    def test_cluster_stop_without_start(self):
        cluster = self._make_one()
        cluster.stop()

    def test_cluster_stop_twice(self):
        cluster = self._make_one()
        cluster.start()
        cluster.stop()
        cluster.stop()

    def test_cluster_terminate(self):
        cluster = self._make_one()
        self.assertTrue(os.path.isdir(cluster.working_path))
        cluster.terminate()
        self.assertFalse(os.path.isdir(cluster.working_path))

    def test_cluster_size_3(self):
        cluster = self._make_one(size=3)
        cluster.start()
        self.assertEqual(len(cluster), 3)
        self.assertEqual(len(cluster.hosts), 3)
        self.assertEqual(len(os.listdir(cluster.working_path)), 3)
        self.assertEqual(len(cluster.address.split(',')), 3)
        client = cluster.client
        self.assertEqual(client.health()['number_of_nodes'], 3)
        # test if routing works and data is actually distributed across nodes
        client.create_index('test_shards', settings={
            'number_of_shards': 1,
            'number_of_replicas': 2,
        })
        client.index('test_shards', 'spam', {'eggs': 'bacon'})
        client.refresh('test_shards')
        shard_info = client.status()['indices']['test_shards']['shards']['0']
        nodes = set([s['routing']['node'] for s in shard_info])
        self.assertEqual(len(nodes), 3)
