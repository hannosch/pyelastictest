from unittest import TestCase

from pyelastictest.cluster import Cluster


class TestIsolated(TestCase):

    def setUp(self):
        self.cluster = Cluster()
        self.cluster.start()

    def tearDown(self):
        self.cluster.terminate()

    def _make_one(self):
        from pyelastictest.isolated import Isolated
        return Isolated()

    def test_index_deletion(self):
        iso = self._make_one()
        iso.setup_es(self.cluster)
        iso.es_client.index('documents', 'doc', {'foo': 1})
        iso.es_client.refresh()
        self.assertEqual(len(iso.es_client.status()['indices']), 1)
        # clean up
        iso.teardown_es()
        self.assertEqual(len(self.cluster.client.status()['indices']), 0)


class TestIsolatedContextManager(TestCase):

    def setUp(self):
        self.cluster = Cluster()
        self.cluster.start()

    def tearDown(self):
        self.cluster.terminate()

    def _get_target(self):
        from pyelastictest.isolated import isolated
        return isolated

    def test_with(self):
        with self._get_target()(cluster=self.cluster) as iso:
            self.assertTrue(iso.es_cluster[0].running)
            iso.es_client.index('documents', 'doc', {'foo': 1})
            iso.es_client.refresh()
            self.assertEqual(len(iso.es_client.status()['indices']), 1)
        self.assertEqual(len(self.cluster.client.status()['indices']), 0)
