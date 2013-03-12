import atexit
import logging
import os
import shutil
import socket
import tempfile
import time
import uuid

from pyelasticsearch.exceptions import ElasticHttpError
from requests.exceptions import RequestException

from pyelastictest.client import ExtendedClient
from pyelastictest.node import Node

CLUSTER = None
PYES_LOGGER = logging.getLogger('pyelasticsearch')
REQUESTS_LOGGER = logging.getLogger('requests.packages.urllib3.connectionpool')


def get_es_path():
    """Return the `ES_PATH` environment variable or raise a `ValueError` if
    the variable isn't found or doesn't point to a directory.
    """
    ES_PATH = os.environ.get('ES_PATH')
    if not ES_PATH or not os.path.isdir(ES_PATH):  # pragma: nocover
        raise ValueError('ES_PATH environment variable must be defined.')
    return ES_PATH


def get_cluster():
    """Get or create a module global cluster.
    """
    global CLUSTER
    if CLUSTER is None:
        CLUSTER = Cluster()
        CLUSTER.start()
    return CLUSTER


def get_free_port(ip='127.0.0.1'):
    """Let the operating system give us a free port.

    :param ip: The ip address of the local machine.
    :type ip: str
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((ip, 0))
        port = sock.getsockname()[1]
    finally:
        sock.close()
    return port


class Cluster(object):
    """An isolated ElasticSearch cluster of a given size.

    The cluster stores all data in a temporary directory, uses a uuid as the
    cluster name and only connects to its own list of nodes. The processes are
    stopped at the end of the test run and the temporary data cleaned up.
    """

    def __init__(self,
                 install_path=None, ip='127.0.0.1', size=1, ports=None):
        """Create an ElasticSearch cluster.

        :param install_path: The filesystem path to an unpacked ElasticSearch
                             tarball. If `None` is specified, the path will
                             be taken from the `ES_PATH` environment variable.
        :type install_path: str
        :param ip: The ip address of the local machine.
        :type ip: str
        :param size: The number of cluster nodes to create.
        :type size: int
        :param ports: An optional list of port tuples. The first value in each
                      tuple is the client port and the second the cluster
                      transport port. By default the code lets the OS choose
                      free ports.
        :type ports: list
        """
        if install_path is None:
            install_path = get_es_path()
        self.install_path = install_path
        self.ip = ip
        self.size = size
        self.name = uuid.uuid4().hex
        self.working_path = tempfile.mkdtemp()
        self.nodes = []
        self.client = None
        self.health_filter = InfoLogFilter()
        # configure cluster ports
        self.configure_ports(size, ports)

    def configure_ports(self, size, ports):
        self.ports = []
        self.transport_ports = []
        if ports is None:
            for i in range(size):
                self.ports.append(get_free_port(self.ip))
                self.transport_ports.append(get_free_port(self.ip))
        elif len(ports) != size:
            raise ValueError("The specified ports didn't match the size.")
        else:
            for port, tport in ports:
                self.ports.append(port)
                self.transport_ports.append(tport)
        self.hosts = ['%s:%s' % (self.ip, p) for p in self.transport_ports]

    @property
    def urls(self):
        """Exposes a list of client urls to connect to all cluster nodes.
        """
        return ['http://%s:%s' % (self.ip, p) for p in self.ports]

    def start(self, timeout=30):
        """Start all cluster nodes and wait for them to be ready.

        :param timeout: Time in seconds to wait for cluster startup to succeed.
        :type timeout: int
        :raises: `OSError` if any of the cluster nodes couldn't be started.
        """
        atexit.register(lambda proc: proc.terminate(), self)
        for i in range(self.size):
            port = self.ports[i]
            transport_port = self.transport_ports[i]
            node = Node(self, '%s_%s' % (self.name, i), port, transport_port)
            self.nodes.append(node)
            node.start()

        self.client = ExtendedClient(self.urls, max_retries=len(self))
        # silence massive log output
        try:
            PYES_LOGGER.addFilter(self.health_filter)
            REQUESTS_LOGGER.addFilter(self.health_filter)
            self.wait_until_ready(timeout)
        finally:
            PYES_LOGGER.removeFilter(self.health_filter)
            REQUESTS_LOGGER.removeFilter(self.health_filter)

    def stop(self):
        """Stop all cluster nodes."""
        for node in self.nodes:
            node.stop()

    def terminate(self):
        """Stop the cluster and remove all working directories.

        This method is automatically called via an `atexit` handler,
        registered in :attr:`Cluster.start`.
        """
        self.stop()
        self.client = None
        shutil.rmtree(self.working_path, ignore_errors=True)

    def wait_until_ready(self, timeout=30):
        time.sleep(2)
        now = time.time()
        while time.time() - now < timeout:
            try:
                # check to see if our process is ready
                health = self.client.health()
            except (ElasticHttpError, RequestException, socket.error):
                # wait a bit before re-trying
                time.sleep(0.5)
            else:
                status_ok = health['status'] == 'green'
                name_ok = health['cluster_name'] == self.name
                size_ok = health['number_of_nodes'] == len(self)
                if status_ok and name_ok and size_ok:
                    break
        else:  # pragma: nocover
            raise OSError("Couldn't start elasticsearch")

    def __getitem__(self, n):
        """Return the zero to n-th cluster node.
        """
        return self.nodes[n]

    def __len__(self):
        """Return the number of cluster nodes.
        """
        return self.size


class InfoLogFilter(logging.Filter):

    def filter(self, record):
        if record.levelno <= logging.INFO:
            return False
        return True
