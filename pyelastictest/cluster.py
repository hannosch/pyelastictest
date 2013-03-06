import atexit
import os
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

    def __init__(self, install_path, size=1):
        self.install_path = install_path
        self.size = size
        self.cluster_id = uuid.uuid4().hex
        self.working_path = tempfile.mkdtemp()
        self.nodes = []

    def start(self):
        for i in range(self.size):
            node = Node(
                self.install_path, self.working_path, self.cluster_id, i)
            self.nodes.append(node)
            node.start()

    def stop(self):
        for node in self.nodes:
            node.stop()

    def terminate(self):
        self.stop()
        shutil.rmtree(self.working_path, ignore_errors=True)
