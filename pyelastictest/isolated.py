from unittest import TestCase

from pyelastictest.cluster import get_cluster


class Isolated(object):

    def setup_es(self):
        self.es_cluster = get_cluster()
        self.es_client = self.es_cluster.client
        self._prior_templates = self._get_template_names()

    def teardown_es(self):
        self._delete_extra_templates()
        self.es_client.delete_all_indexes()

    def _delete_extra_templates(self):
        current_templates = self._get_template_names()
        for t in current_templates - self._prior_templates:
            self.es_cluster.client.delete_template(t)

    def _get_template_names(self):
        return set(self.es_cluster.client.list_templates().keys())


class IsolatedTestCase(TestCase, Isolated):

    def setUp(self):
        self.setup_es()

    def tearDown(self):
        self.teardown_es()
