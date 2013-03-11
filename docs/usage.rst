.. _usage:

=====
Usage
=====

pyelastictest provides a helper class to manage a temporary ElasticSearch
cluster and provides full test isolation between test runs.

The test helper needs to be able to find an ElasticSearch installation. You
need to specify an environment variable called `ES_PATH` and point it at the
location. The directory should contain bin and lib directories.

By default everything uses a module global ElasticSearch cluster with a single
node. You can configure different settings and use multiple clusters in the
same test suite if you really want to.


Isolated
========

The :class:`~pyelastictest.isolated.Isolated` class can be used directly or
mixed in with your test code.

Example:

.. code-block:: python

    import unittest

    from pyelasticsearch import ElasticSearch
    from pyelastictest import Isolated


    class MyTestCase(unittest.TestCase, Isolated):

        def setUp(self):
            self.setup_es()

        def tearDown(self):
            self.teardown_es()

        def test_mycode(self):
            es = ElasticSearch(self.es_cluster.urls)
            es.index('test_index', 'test_type', {'foo': 1})
            ...


Test Case
=========

The :class:`~pyelastictest.isolated.IsolatedTestCase` is complete test case that
is equivalent to the mix-in setup of a standard `unittest.TestCase` and
:class:`~pyelastictest.isolated.Isolated`. An equivalent test to the
one above:

.. code-block:: python

    from pyelasticsearch import ElasticSearch
    from pyelastictest import IsolatedTestCase

    class MyTestCase(IsolatedTestCase):

        def test_mycode(self):
            es = ElasticSearch(self.es_cluster.urls)
            es.index('test_index', 'test_type', {'foo': 1})
            ...


Context manager
===============

If you want finer control, you can also use the isolation via a context
manager. The :class:`~pyelastictest.isolated.Isolated` class stores the
before and after state of the ElasticSearch cluster and resets the state:


.. code-block:: python

    from unittest import TestCase

    from pyelasticsearch import ElasticSearch
    from pyelastictest.cluster import Cluster
    from pyelastictest.isolated import isolated


    class MyTestCase(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.cluster = Cluster(size=3)
            cls.cluster.start()

        @classmethod
        def tearDownClass(cls):
            cls.cluster.terminate()

        def test_mycode(self):
            with isolated(cluster=self.cluster) as iso:
                es = ElasticSearch(iso.es_cluster.urls)
                es.index('test_index', 'test_type', {'foo': 1})
                ...
