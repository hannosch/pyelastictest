import os
import os.path
import shutil
import subprocess
import tempfile


CONF = """\
cluster.name: "{cluster_name}"
node.name: "{node_name}"
index.number_of_shards: 1
index.number_of_replicas: 0
http.port: {port}
transport.tcp.port: {tport}
discovery.zen.ping.multicast.enabled: false
discovery.zen.ping.unicast.hosts: {hosts}
path.conf: {config_path}
path.work: {working_path}
path.plugins: {working_path}
path.data: {data_path}
path.logs: {log_path}
"""

LOG_CONF = """\
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


class Node(object):
    """Start a new ElasticSearch node, isolated in a temporary
    directory and part of a cluster.
    """

    def __init__(self, cluster, name, port):
        self.cluster = cluster
        self.working_path = tempfile.mkdtemp(dir=cluster.working_path)
        self.name = name
        self.port = port
        self.address = 'http://localhost:' + str(port)
        self.running = False
        self.process = None

    def start(self):
        install_path = self.cluster.install_path
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
        es_bin_dir = os.path.join(install_path, 'bin')
        shutil.copy(os.path.join(es_bin_dir, 'elasticsearch'), bin_path)
        shutil.copy(os.path.join(es_bin_dir, 'elasticsearch.in.sh'), bin_path)

        # write configuration file
        with open(conf_path, "w") as config:
            config.write(CONF.format(
                cluster_name=self.cluster.name,
                node_name=self.name,
                port=self.port,
                tport=self.port + 1,
                hosts=','.join(self.cluster.hosts),
                working_path=self.working_path,
                config_path=config_path,
                data_path=data_path,
                log_path=log_path,
            ))

        # write log file
        with open(log_conf_path, "w") as config:
            config.write(LOG_CONF)

        # setup environment, copy from base process
        environ = os.environ.copy()
        # configure explicit ES_INCLUDE, to prevent fallback to
        # system-wide locations like /usr/share, /usr/local/, ...
        environ['ES_INCLUDE'] = os.path.join(bin_path, 'elasticsearch.in.sh')
        lib_dir = os.path.join(install_path, 'lib')
        # let the process find our jar files first
        path = '{dir}/elasticsearch-*:{dir}/*:{dir}/sigar/*:$ES_CLASSPATH'
        environ['ES_CLASSPATH'] = path.format(dir=lib_dir)

        self.process = subprocess.Popen(
            args=[bin_path + "/elasticsearch", "-f",
                  "-Des.config=" + conf_path],
            # stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environ
        )
        self.running = True

    def stop(self):
        try:
            self.process.terminate()
        except OSError:
            # might not have been running
            pass
        else:
            self.process.wait()
        self.running = False


class ESTestHarness(object):

    def setup_es(self):
        from pyelastictest.cluster import get_cluster
        self.es_cluster = get_cluster()
        self._prior_templates = self._get_template_names()

    def teardown_es(self):
        self._delete_extra_templates()
        self.es_cluster.reset()

    def _delete_extra_templates(self):
        current_templates = self._get_template_names()
        for t in current_templates - self._prior_templates:
            self.es_cluster.client.delete_template(t)

    def _get_template_names(self):
        return set(self.es_cluster.client.list_templates().keys())
