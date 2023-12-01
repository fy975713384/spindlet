from spindlet.database import MySQLEngine
from spindlet.utils import logger as logger_util

from .context import Context
from .meta import KeywordMeta


class KeywordBase(metaclass=KeywordMeta):

    def __init__(self, env, logger=None, log_level="DEBUG", log_path=None):
        super(KeywordBase, self).__init__()
        self.env: str = env.strip().upper()
        self.logger = logger or logger_util.get_logger(log_level, log_path)
        self.ctx = Context()

    def db(self, **db_options) -> MySQLEngine:
        pass

    def gen_biz_seq(self) -> str:
        pass
