from pyelasticsearch import ElasticSearch
from pyelasticsearch.client import es_kwargs


class ExtendedClient(ElasticSearch):
    """Wrapper around pyelasticsearch's client to add some missing
    API's. These should be merged upstream.
    """

    @es_kwargs()
    def create_template(self, name, settings, query_params=None):
        """
        Create an index template.

        :arg name: The name of the template.
        :arg settings: A dictionary of settings.

        See `ES's index-template API`_ for more detail.

        .. _`ES's index-template API`:
           http://tinyurl.com/es-index-template
        """
        return self.send_request('PUT', ['_template', name], settings,
                                 query_params=query_params)

    @es_kwargs()
    def delete_template(self, name, query_params=None):
        """
        Delete an index template.

        :arg name: The name of the template.

        See `ES's index-template API`_ for more detail.

        .. _`ES's index-template API`:
            http://tinyurl.com/es-index-template
        """
        return self.send_request('DELETE', ['_template', name],
                                 query_params=query_params)

    @es_kwargs()
    def get_template(self, name, query_params=None):
        """
        Get the settings of an index template.

        :arg name: The name of the template.

        See `ES's index-template API`_ for more detail.

        .. _`ES's index-template API`:
            http://tinyurl.com/es-index-template
        """
        return self.send_request('GET', ['_template', name],
                                 query_params=query_params)

    def list_templates(self):
        """
        Get a dictionary with all index template settings.

        See `ES's index-template API`_ for more detail.

        .. _`ES's index-template API`:
            http://tinyurl.com/es-index-template
        """
        res = self.cluster_state(filter_routing_table=True,
                                 filter_nodes=True, filter_blocks=True)
        return res['metadata']['templates']

    @es_kwargs('filter_nodes', 'filter_routing_table', 'filter_metadata',
               'filter_blocks', 'filter_indices')
    def cluster_state(self, query_params=None):
        """
        The cluster state API allows to get a comprehensive state
        information of the whole cluster.

        :arg query_params: A map of querystring param names to values or
            ``None``

        See `ES's cluster-state API`_ for more detail.

        .. _`ES's cluster-state API`:
           http://tinyurl.com/cluster-state
        """
        return self.send_request(
            'GET', ['_cluster', 'state'], query_params=query_params)

    @es_kwargs()
    def multi_get(self, index=None, doc_type=None, body=None,
                  query_params=None):
        if not body:
            # keep index and doc_type as first arguments,
            # but require body
            raise ValueError('A body is required.')

        return self.send_request(
            'GET',
            [self._concat(index), self._concat(doc_type), '_mget'],
            body,
            query_params=query_params)