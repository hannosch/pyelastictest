from requests.exceptions import ConnectionError
from pyelasticsearch import ElasticSearch

from pyelastictest import IsolatedTestCase
from pyelastictest.cluster import Cluster


class TestIsolatedTestCase(IsolatedTestCase):

    def setUp(self):
        self.cluster = Cluster(size=3)
        self.cluster.start()

    def tearDown(self):
        self.cluster.terminate()

    def test_start_stop(self):
        es = ElasticSearch(reversed(self.cluster.urls))

        def es_health():
            for i in range(3):
                try:
                    return es.health()
                except ConnectionError:
                    pass

        self.cluster[0].stop()
        self.assertEqual(es_health()['number_of_nodes'], 2)
