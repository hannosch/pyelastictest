import os

from unittest import TestCase


class TestCluster(TestCase):

    def setUp(self):
        self._cluster = None

    def tearDown(self):
        if self._cluster:
            self._cluster.terminate()

    def _make_one(self, size=1):
        from pyelastictest import cluster
        es_path = cluster.get_es_path()
        self._cluster = cluster.Cluster(es_path, size=size)
        return self._cluster

    def test_cluster_init(self):
        cluster = self._make_one()
        self.assertEqual(cluster.nodes, [])

    def test_cluster_start(self):
        cluster = self._make_one()
        cluster.start()

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
