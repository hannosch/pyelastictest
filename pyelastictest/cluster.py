import atexit
import os
import random
import shutil
import socket
import tempfile
import time
import uuid

from pyelastictest.client import ExtendedClient
from pyelastictest.node import Node

CLUSTER = None


def get_es_path():
    ES_PATH = os.environ.get('ES_PATH')
    if not ES_PATH:  # pragma: nocover
        raise ValueError('ES_PATH environment variable must be defined.')
    return ES_PATH


def get_cluster():
    global CLUSTER
    if CLUSTER is None:
        ES_PATH = get_es_path()
        CLUSTER = Cluster(ES_PATH)
        CLUSTER.start()
        atexit.register(lambda proc: proc.terminate(), CLUSTER)
    return CLUSTER


def get_free_port(retry=10):
    sock = None
    for i in range(retry):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', 0))
        except socket.error:
            sock.close()
        else:
            break
    port = sock.getsockname()[1]
    sock.close()
    return port


class Cluster(object):

    def __init__(self, install_path, size=1):
        self.install_path = install_path
        self.size = size
        self.name = uuid.uuid4().hex
        self.working_path = tempfile.mkdtemp()
        self.nodes = []
        self.client = None
        # configure cluster ports
        self.ports = []
        self.trans_ports = []
        for i in range(size):
            self.ports.append(get_free_port())
            self.trans_ports.append(get_free_port())
        self.hosts = ['localhost:%s' % p for p in self.trans_ports]

    def start(self):
        for i in range(self.size):
            port = self.ports[i]
            trans_port = self.trans_ports[i]
            node = Node(self, '%s_%s' % (self.name, i), port, trans_port)
            self.nodes.append(node)
            node.start()

        self.client = ExtendedClient(
            [n.address for n in self.nodes], max_retries=1)
        self.wait_until_ready()

    def stop(self):
        for node in self.nodes:
            node.stop()

    def terminate(self):
        self.stop()
        self.client = None
        shutil.rmtree(self.working_path, ignore_errors=True)

    def wait_until_ready(self):
        now = time.time()
        while time.time() - now < 30:
            try:
                # check to see if our process is ready
                health = self.client.health()
            except Exception:
                # wait a bit before re-trying
                time.sleep(0.5)
            else:
                status_ok = health['status'] == 'green'
                name_ok = health['cluster_name'] == self.name
                size_ok = health['number_of_nodes'] == len(self)
                if status_ok and name_ok and size_ok:
                    break
        else:
            raise OSError("Couldn't start elasticsearch")

    def reset(self):
        if self.client is None:
            return
        # cleanup all indices after each test run
        self.client.delete_all_indexes()

    def __getitem__(self, i):
        return self.nodes[i]

    def __len__(self):
        return self.size
