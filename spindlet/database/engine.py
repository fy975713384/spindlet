from typing import Any, List, Mapping, Optional, Sequence
from typing import Protocol, runtime_checkable

import pymysql
from dbutils.persistent_db import PersistentDB
from loguru import logger
from pydantic import BaseModel, conint, constr, ValidationError, model_validator
from pymysql.cursors import DictCursor
from pypika import MySQLQuery


@runtime_checkable
class _SQLRenderable(Protocol):
    def get_sql(self) -> str:
        ...


SQLParams = Sequence[Any] | Mapping[str, Any]


class DBOptionsError(Exception):
    pass


class _InstanceGen:
    """ 生成链式实例调用 """

    def __init__(self, trigger_method, method_name: str, instance: object):
        self.__trigger_method = trigger_method
        self.__method_name = method_name
        self.__instance = instance

    def __getattr__(self, method_name):
        self.__method_name = method_name
        return self

    def __call__(self, *args, **kwargs):
        if self.__method_name == 'execute':
            return self.__trigger_method('execute', self.__instance, **kwargs)
        else:
            self.__instance = getattr(self.__instance, self.__method_name)(*args, **kwargs)
            return self


class _Method:

    def __getattr__(self, item):
        return _InstanceGen(self.__trigger, item, instance=MySQLQuery)

    def __trigger(self, method, instance, **kwargs):
        return getattr(self, method)(instance, **kwargs)


class _DBOptions(BaseModel):
    host: constr(min_length=1, strip_whitespace=True)
    port: conint(strict=False, ge=1, le=65535) = 3306
    user: Optional[constr(min_length=1, strip_whitespace=True)] = None
    username: Optional[constr(min_length=1, strip_whitespace=True)] = None
    password: constr(min_length=1, strip_whitespace=True)
    database: Optional[constr(min_length=1, strip_whitespace=True)] = None

    @model_validator(mode="before")
    @classmethod
    def fill_defaults(cls, data: dict):
        # 自动填充 username
        if not data.get("username"):
            if data.get("user"):
                data["username"] = data["user"]
            else:
                raise ValueError("user/username 必须传一个")
        return data


class _Engine:
    def __init__(self, **db_options):
        try:
            self._db_options = _DBOptions(**db_options)
        except ValidationError as e:
            raise DBOptionsError(e.__str__()) from None
        self._db_conn: Optional[PersistentDB] = None

    def _conn(self):
        raise NotImplementedError

    def _execute(self, sql: str, params: Optional[SQLParams], commit=True):
        raise NotImplementedError

    @staticmethod
    def _normalize_sql(sql: Any) -> str:
        if isinstance(sql, str):
            return sql
        if isinstance(sql, _SQLRenderable):
            return sql.get_sql()
        return str(sql)

    def create_conn(self):
        if not self._db_conn:
            self._db_conn = self._conn()
        try:
            return self._db_conn.connection(shareable=False)
        except pymysql.err.OperationalError as e:
            if e.args[0] == 1045:
                err_msg = (f'数据库<{self._db_options.database}>用户名或密码不正确：'
                           f'{self._db_options.username}:{self._db_options.password[:2]}??????')
            else:
                err_msg = e
            raise DBOptionsError(err_msg) from None

    def execute(self, sql, commit=True, debug=False, params: Optional[SQLParams] = None):
        sql = self._normalize_sql(sql)
        debug and logger.debug(f'数据库连接信息：'
                               f'{self._db_options.username}:{self._db_options.password[:2]}??????'
                               f'@{self._db_options.host}:{self._db_options.port}')
        debug and logger.debug(f'开始执行 SQL：{sql}')
        debug and params and logger.debug(f'SQL 参数：{params}')
        try:
            query = self._execute(sql, params, commit)
        except Exception as e:
            logger.error(
                f'SQL语句执行异常<{self._db_options.host}:{self._db_options.port}@{self._db_options.database}>：'
                f'{sql}')
            raise e
        return _Query(query)

    def commit(self):
        self._db_conn and self._db_conn.dedicated_connection().commit()

    def close_conn(self):
        self._db_conn and self._db_conn.dedicated_connection().close()
        self._db_conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close_conn()


class _Query:
    def __init__(self, res: List[dict]):
        self.res = res

    def fetchone(self, first: bool = False):
        res: dict = self.res[0] if self.res else {}
        return res if not first else (list(res.values())[0] if res else None)

    def fetchmany(self, num: int):
        return self.res[:int(num)]

    def fetchall(self, flat: bool = False):
        if flat and self.res and len(self.res[0]) == 1:
            return [list(_.values())[0] for _ in self.res]
        return self.res


class MySQLEngine(_Engine, _Method):

    def _conn(self):
        return PersistentDB(
            creator=pymysql, setsession=[],
            host=self._db_options.host,
            port=int(self._db_options.port),
            user=self._db_options.username,
            password=self._db_options.password,
            database=self._db_options.database
        )

    def _execute(self, sql: str, params: Optional[SQLParams], commit=True):
        conn = self.create_conn()
        exe_err = None
        try:
            with conn.cursor(cursor=DictCursor) as cursor:
                if params is None:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, params)
                query = cursor.fetchall()
            commit and conn.commit()
            return query
        except Exception as e:
            exe_err = e
            conn.ping(True)
            conn.rollback()
        finally:
            if self._db_conn and (exe_err or commit):
                conn.close()
        raise exe_err


class HiveEngine(_Engine):
    """ Hive 数据库引擎，依赖 pyhive/thrift_sasl """

    def _conn(self):
        try:
            from pyhive import hive  # noqa
            import thrift as _  # noqa
            import thrift_sasl as _  # noqa
        except ImportError as e:
            raise DBOptionsError(
                f'Hive 连接依赖未安装：{e.name}，请执行 pip install thrift_sasl thrift PyHive'
            ) from None
        return PersistentDB(
            creator=hive.connect, setsession=[],
            host=str(self._db_options.host),
            port=int(self._db_options.port),
            username=self._db_options.username,
            password=self._db_options.password,
            database=self._db_options.database,
            auth='LDAP',
        )

    def _execute(self, sql: str, params: Optional[SQLParams], commit=True):
        conn = self.create_conn()
        exe_err = None
        try:
            with conn.cursor() as cursor:
                if params is None:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, params)
                fields = [_[0] for _ in cursor.description]
                res = cursor.fetchall()
                query = [dict(zip(fields, row)) for row in res]
            commit and conn.commit()
            return query
        except Exception as e:
            exe_err = e
        finally:
            if self._db_conn and (exe_err or commit):
                conn.close()
        raise exe_err
