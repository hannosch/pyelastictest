import atexit
import os
import random
import shutil
import tempfile
import uuid

from pyelastictest.node import Node

CLUSTER = None


def get_es_path():
    ES_PATH = os.environ.get('ES_PATH')
    if not ES_PATH:
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


class Cluster(object):

    def __init__(self, install_path, size=1, port_base=19000):
        self.install_path = install_path
        self.size = size
        self.name = uuid.uuid4().hex
        self.working_path = tempfile.mkdtemp()
        self.nodes = []
        # configure cluster ports
        self.port_base = port_base + random.randint(0, 90) * 10
        self.ports = []
        port = self.port_base
        for i in range(size):
            port += i * 10
            self.ports.append(port)
        self.hosts = ['localhost:' + str(p + 1) for p in self.ports]

    def start(self):
        for i in range(self.size):
            port = self.ports[i]
            node = Node(self, '%s_%s' % (self.name, i), port)
            self.nodes.append(node)
            node.start()

    def stop(self):
        for node in self.nodes:
            node.stop()

    def terminate(self):
        self.stop()
        shutil.rmtree(self.working_path, ignore_errors=True)

    def __getitem__(self, i):
        return self.nodes[i]

    def __len__(self):
        return self.size
