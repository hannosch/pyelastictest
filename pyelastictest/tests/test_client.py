from pyelastictest import IsolatedTestCase


class TestExtendedClient(IsolatedTestCase):

    def _make_one(self):
        from pyelastictest import client
        return client.ExtendedClient(self.es_cluster.urls)

    def test_create_template(self):
        client = self._make_one()
        client.create_template('template1', {
            'template': 'test_index_*',
            'settings': {
                'number_of_shards': 3,
            },
        })
        # make sure an index matching the pattern gets the shard setting
        client.create_index('test_index_1')
        self.assertEqual(client.status('test_index_1')['_shards']['total'], 3)

    def test_delete_template(self):
        client = self._make_one()
        client.create_template('template2', {
            'template': 'test_index',
        })
        client.delete_template('template2')
        self.assertFalse(client.get_template('template2'))

    def test_get_template(self):
        client = self._make_one()
        client.create_template('template3', {
            'template': 'test_index',
        })
        res = client.get_template('template3')
        self.assertEqual(res['template3']['template'], 'test_index')

    def test_list_templates(self):
        client = self._make_one()
        client.create_template('t1', {'template': 'test1'})
        client.create_template('t2', {'template': 'test2'})
        client.create_template('t3', {'template': 'test3'})
        res = client.list_templates()
        self.assertEqual(len(res), 3)
        self.assertEqual(set(res.keys()), set(['t1', 't2', 't3']))

    def test_cluster_state(self):
        client = self._make_one()
        res = client.cluster_state(filter_routing_table=True)
        self.assertTrue('nodes' in res)
        self.assertFalse('routing_table' in res)
