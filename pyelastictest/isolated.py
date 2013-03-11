from unittest import TestCase

from pyelastictest.cluster import get_cluster


class Isolated(object):
    """Provides test data isolation for a running
    :class:`pyelastictest.cluster.Cluster`.

    Currently it deletes all indexes on teardown. Prior existing templates
    will be detected and left alone. All extra templates will be removed.
    Changes to prior templates aren't detected nor are changes to cluster
    settings.
    """

    def setup_es(self, cluster=None):
        """Setup isolation and capture current state of the cluster.

        :param cluster: Specifies the cluster, if none is specifies
                        calls :attr:`~pyelastictest.cluster.get_cluster`
                        to get or create a module global cluster.
        :type cluster: :class:`pyelastictest.cluster.Cluster`

        """
        if cluster is None:
            cluster = get_cluster()
        self.es_cluster = cluster
        self.es_client = self.es_cluster.client
        self._prior_templates = self._get_template_names()

    def teardown_es(self):
        """Returns the cluster to its prior state and deletes all indexes.
        """
        self._delete_extra_templates()
        self.es_client.delete_all_indexes()

    def _delete_extra_templates(self):
        current_templates = self._get_template_names()
        for t in current_templates - self._prior_templates:
            self.es_cluster.client.delete_template(t)

    def _get_template_names(self):
        return set(self.es_cluster.client.list_templates().keys())


class IsolatedTestCase(TestCase, Isolated):
    """A test case with the :attr:`Isolated` class mixed in.

    Setup and teardown methods are called to provide test data isolation.
    """

    def setUp(self):
        """Calls :attr:`Isolated.setup_es`."""
        super(IsolatedTestCase, self).setUp()
        self.setup_es()

    def tearDown(self):
        """Calls :attr:`Isolated.teardown_es`."""
        self.teardown_es()
        super(IsolatedTestCase, self).tearDown()
