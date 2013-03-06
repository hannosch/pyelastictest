from unittest import TestCase

from pyelastictest.node import ESTestHarness


class TestESTestHarness(TestCase, ESTestHarness):

    def setUp(self):
        self.setup_es()

    def tearDown(self):
        self.teardown_es()
