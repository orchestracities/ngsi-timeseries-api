from pathlib import Path
import os
from threading import Thread
from typing import Any

from cache.factory import CACHE_QUERIES_ENV_VAR, REDIS_HOST_ENV_VAR
from geocoding.factory import USE_GEOCODING_ENV_VAR
import server.wsgi as flask
from translators.factory import QL_CONFIG_ENV_VAR
from translators.timescale import POSTGRES_HOST_ENV_VAR


class ServerConfig:
    # NOTE. GH #10 calls for consolidated configuration, which is
    # a good thing. When that happens, we can zap this class.
    # - https://github.com/orchestracities/ngsi-timeseries-api/issues/10#issuecomment-383876491

    @staticmethod
    def set_env_var(name: str, value: Any):
        if name in os.environ and os.environ[name]:  # (*)
            return
        os.environ[name] = str(value)
    # NOTE. Default env. Env vars defined in setup_dev_env.sh should take
    # precedence. In fact, the script sets up host env vars, so we won't
    # override them if set.

    @staticmethod
    def yaml_config_path() -> str:
        base = Path(__file__).parent.absolute()
        config_file = base / 'ql-config.yml'
        return os.fspath(config_file)
        # '/abs/path/to/src/reporter/tests/ql-config.yml'

    def set_ql_config_env_var(self):
        self.set_env_var(QL_CONFIG_ENV_VAR, self.yaml_config_path())

    def set_geo_coding_env_var(self):
        self.set_env_var(USE_GEOCODING_ENV_VAR, False)

    def set_cache_queries_env_var(self):
        self.set_env_var(CACHE_QUERIES_ENV_VAR, True)

    def set_log_level_env_var(self):
        self.set_env_var('LOGLEVEL', 'INFO')

    def set_redis_host_env_var(self):
        self.set_env_var(REDIS_HOST_ENV_VAR, 'localhost')

    def set_postgres_host_env_var(self):
        self.set_env_var(POSTGRES_HOST_ENV_VAR, 'localhost')

    def set_env(self):
        self.set_ql_config_env_var()
        self.set_geo_coding_env_var()
        self.set_cache_queries_env_var()
        self.set_log_level_env_var()
        self.set_redis_host_env_var()
        self.set_postgres_host_env_var()


def start_embedded_flask():
    ServerConfig().set_env()

    t = Thread(target=flask.run, args=())
    t.daemon = True                        # (*)
    t.start()

# NOTE. Daemon thread. This makes sure the program won't wait on this
# thread to complete before exiting, which is what we want b/c of the
# infinite loop in the run method. The downside is that when the Python
# interpreter quits, this thread will be interrupted abruptly.
