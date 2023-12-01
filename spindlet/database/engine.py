from ipaddress import IPv4Address
from typing import Optional, List

import pymysql
from dbutils.persistent_db import PersistentDB
from loguru import logger
from pydantic import BaseModel, conint, model_validator, constr, ValidationError
from pymysql.cursors import DictCursor
from pypika import MySQLQuery


class DBOptionsError(Exception):
    pass


class _InstanceGen:

    def __init__(self, trigger_method, method_name, instance):
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
        return getattr(self, method)(str(instance), **kwargs)


class _DBOptions(BaseModel):
    ip: Optional[IPv4Address] = None
    host: Optional[IPv4Address] = None
    port: conint(strict=False, ge=1, le=65535) = 3306
    user: Optional[constr(min_length=1, strip_whitespace=True)] = None
    username: Optional[constr(min_length=1, strip_whitespace=True)] = None
    password: constr(min_length=1, strip_whitespace=True)
    database: Optional[constr(min_length=1, strip_whitespace=True)] = None

    @model_validator(mode='before')
    def ip_host_2c1(self):
        if not (self.get('ip') or self.get('host')):
            raise ValueError('one of ip/host must be provided')
        return self

    @model_validator(mode='before')
    def user_username_2c1(self):
        if not (self.get('user') or self.get('username')):
            raise ValueError('one of user/username must be provided')
        return self


class _Engine:
    def __init__(self, **db_options):
        try:
            self._db_options = _DBOptions(**db_options)
        except ValidationError as e:
            raise DBOptionsError(e.__str__()) from None
        self._db_conn: Optional[PersistentDB] = None

    def _conn(self):
        raise NotImplementedError

    def _execute(self, sql, commit=True):
        raise NotImplementedError

    def create_conn(self):
        if not self._db_conn:
            self._db_conn = self._conn()
        return self._db_conn.connection(shareable=False)

    def execute(self, sql, commit=True, debug=False):
        debug and logger.debug(f'数据库连接信息：'
                               f'{self._db_options.username}:{self._db_options.password[:2]}??????'
                               f'@{self._db_options.host}:{self._db_options.port}')
        debug and logger.debug(f'开始执行 SQL：{sql}')
        query = self._execute(sql, commit)
        return QueryResult(query)

    def commit(self):
        self._db_conn and self._db_conn.dedicated_connection().commit()

    def close_conn(self):
        self._db_conn and self._db_conn.dedicated_connection().close()
        self._db_conn = None


class QueryResult:
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

    def _execute(self, sql, commit=True):
        conn = self.create_conn()
        exe_err = None
        try:
            with conn.cursor(cursor=DictCursor) as cursor:
                cursor.execute(sql)
                query = cursor.fetchall()
            commit and conn.commit()
            return query
        except Exception as e:
            exe_err = e
            conn.rollback()
        finally:
            if self._db_conn and (exe_err or commit):
                conn.close()
        raise exe_err
