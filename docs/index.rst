=============
pyelastictest
=============

pyelastictest provides a test harness for Python integration tests against a
real ElasticSearch server.

It creates a local ElasticSearch cluster in a temporary directory and runs it
as a subprocess. The cluster is isolated from any other ElasticSearch cluster
via a locked-down configuration.

By default the API's use a module global ElasticSearch cluster with a single
node. You can configure different settings and use multiple clusters in the
same test suite if you really want to.

The different API's in the isolated module provide setup and teardown methods
to isolate each test method and provide a clean state.

`pyelasticsearch <https://pyelasticsearch.readthedocs.org>`_ is used as the
client library, but the resulting ElasticSearch cluster is available via the
standard HTTP API and usable by any other library.

Reference Docs
==============

.. toctree::
   :maxdepth: 1

   usage
   api
   changelog

Source Code
===========

All source code is available on `github under pyelastictest
<https://github.com/hannosch/pyelastictest>`_.

Bugs/Support
============

Bugs and support issues should be reported on the `pyelastictest github issue
tracker <https://github.com/hannosch/pyelastictest/issues>`_.

License
=======

``pyelastictest`` is offered under the Apache License 2.0.
