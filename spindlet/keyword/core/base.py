from itertools import zip_longest
from typing import Type

from spindlet.utils import logger as logger_util
from .meta import KeywordMeta
from .store import KeywordStore
from ...database.engine import HiveEngine, MySQLEngine


class KeywordBase(metaclass=KeywordMeta):

    def __init__(self, env, logger=None, log_level="DEBUG", log_path=None):
        super(KeywordBase, self).__init__()
        self.__env_info = self.parse_env(env)
        self.logger = logger or logger_util.get_logger(log_level, log_path)
        self.store = KeywordStore()

    @staticmethod
    def parse_env(env):
        if not isinstance(env, str) or not env.strip():
            raise ValueError("env must be a non-empty string")
        return dict(zip_longest(("env", "cloud", "pt"), env.strip().upper().split("_"), fillvalue=None))

    @property
    def env(self):
        return self.__env_info["env"]

    @property
    def cloud(self):
        return self.__env_info["cloud"]

    @property
    def pt(self):
        return self.__env_info["pt"]

    def db(self, **db_options) -> MySQLEngine:
        """Create a MySQL/TDSQL database engine."""
        return self.__create_db_engine(MySQLEngine, db_options)

    def tidb(self, **db_options) -> MySQLEngine:
        """Create a TiDB database engine using the MySQL-compatible protocol."""
        return self.__create_db_engine(MySQLEngine, db_options)

    def hvdb(self, **db_options) -> HiveEngine:
        """Create a Hive database engine."""
        return self.__create_db_engine(HiveEngine, db_options)

    @staticmethod
    def __create_db_engine(engine_cls: Type[MySQLEngine | HiveEngine], db_options: dict):
        if not db_options:
            raise ValueError("database options must not be empty")
        return engine_cls(**db_options)

    def gen_biz_seq(self) -> str:
        """Generate a business sequence; subclasses should override this as needed."""
        raise NotImplementedError("gen_biz_seq must be implemented by subclasses")
