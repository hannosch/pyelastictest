import atexit
import os
import os.path
import random
import shutil
import subprocess
import tempfile
import time

from pyelastictest.client import ExtendedClient


ES_PROCESS = None


def get_global_es():
    """Get or start a new isolated ElasticSearch process.
    """
    global ES_PROCESS
    if ES_PROCESS is None:
        ES_HOME = os.environ.get('ES_PATH')
        if not ES_HOME:
            raise ValueError('ES_PATH environment variable must be defined.')
        ES_PROCESS = ESProcess(ES_HOME)
        ES_PROCESS.start()
        atexit.register(lambda proc: proc.stop(), ES_PROCESS)
    return ES_PROCESS


_CONF = """\
cluster.name: test
node.name: "test_1"
index.number_of_shards: 1
index.number_of_replicas: 0
http.port: {port}
transport.tcp.port: {tport}
discovery.zen.ping.multicast.enabled: false
path.conf: {config_path}
path.work: {work_path}
path.plugins: {work_path}
path.data: {data_path}
path.logs: {log_path}
"""

_CONF2 = """\
rootLogger: INFO, console, file

logger:
  action: DEBUG

appender:
  console:
    type: console
    layout:
      type: consolePattern
      conversionPattern: "[%d{ISO8601}][%-5p][%-25c] %m%n"

  file:
    type: dailyRollingFile
    file: ${path.logs}/${cluster.name}.log
    datePattern: "'.'yyyy-MM-dd"
    layout:
      type: pattern
      conversionPattern: "[%d{ISO8601}][%-5p][%-25c] %m%n"
"""


class ESProcess(object):
    """Start a new ElasticSearch process, isolated in a temporary
    directory. By default it's configured to listen on localhost and
    a random port between 9201 and 9298. The internal cluster transport
    port is the port number plus 1.
    """

    def __init__(self, install_path, host='localhost', port_base=9200):
        self.install_path = install_path
        self.host = host
        self.port = port_base + random.randint(1, 98)
        self.address = 'http://%s:%s' % (self.host, self.port)
        self.working_path = None
        self.process = None
        self.running = False
        self.client = None

    def start(self):
        """Start a new ES process and wait until it's ready.
        """
        self.working_path = tempfile.mkdtemp()
        bin_path = os.path.join(self.working_path, "bin")
        config_path = os.path.join(self.working_path, "config")
        conf_path = os.path.join(config_path, "elasticsearch.yml")
        log_path = os.path.join(self.working_path, "logs")
        log_conf_path = os.path.join(config_path, "logging.yml")
        data_path = os.path.join(self.working_path, "data")

        # create temporary directory structure
        for path in (bin_path, config_path, log_path, data_path):
            if not os.path.exists(path):
                os.mkdir(path)

        # copy ES startup scripts
        es_bin_dir = os.path.join(self.install_path, 'bin')
        shutil.copy(os.path.join(es_bin_dir, 'elasticsearch'), bin_path)
        shutil.copy(os.path.join(es_bin_dir, 'elasticsearch.in.sh'), bin_path)

        # write configuration file
        with open(conf_path, "w") as config:
            config.write(_CONF.format(port=self.port, tport=self.port + 1,
                                      work_path=self.working_path,
                                      config_path=config_path,
                                      data_path=data_path, log_path=log_path))

        # write log file
        with open(log_conf_path, "w") as config:
            config.write(_CONF2)

        # setup environment, copy from base process
        environ = os.environ.copy()
        # configure explicit ES_INCLUDE, to prevent fallback to
        # system-wide locations like /usr/share, /usr/local/, ...
        environ['ES_INCLUDE'] = os.path.join(bin_path, 'elasticsearch.in.sh')
        lib_dir = os.path.join(self.install_path, 'lib')
        # let the process find our jar files first
        path = '{dir}/elasticsearch-*:{dir}/*:{dir}/sigar/*:$ES_CLASSPATH'
        environ['ES_CLASSPATH'] = path.format(dir=lib_dir)

        self.process = subprocess.Popen(
            args=[bin_path + "/elasticsearch", "-f",
                  "-Des.config=" + conf_path],
            #stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environ
        )
        self.running = True
        self.client = ExtendedClient(self.address)
        self.wait_until_ready()

    def stop(self):
        """Stop the ES process and removes the temporary directory.
        """
        self.process.terminate()
        self.running = False
        self.process.wait()
        shutil.rmtree(self.working_path, ignore_errors=True)

    def wait_until_ready(self):
        now = time.time()
        while time.time() - now < 30:
            try:
                # check to see if our process is ready
                health = self.client.health()
                status = health['status']
                name = health['cluster_name']
                if status == 'green' and name == 'test':
                    break
            except Exception:
                # wait a bit before re-trying
                time.sleep(0.5)
        else:
            self.client = None
            raise OSError("Couldn't start elasticsearch")

    def reset(self):
        if self.client is None:
            return
        # cleanup all indices after each test run
        self.client.delete_all_indexes()


class ESTestHarness(object):

    def setup_es(self):
        self.es_process = get_global_es()
        self._prior_templates = self._get_template_names()

    def teardown_es(self):
        self._delete_extra_templates()
        self.es_process.reset()

    def _delete_extra_templates(self):
        current_templates = self._get_template_names()
        for t in current_templates - self._prior_templates:
            self.es_process.client.delete_template(t)

    def _get_template_names(self):
        return set(self.es_process.client.list_templates().keys())
