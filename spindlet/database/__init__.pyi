from typing import (overload, Text, Any, List, Dict)

from pypika import MySQLQuery, Database, Table, Tables, Interval, Order, EmptyCriterion

__all__ = [
    'MySQLEngine',
    'MySQLQuery', 'Database', 'Table', 'Tables', 'Interval', 'Order', 'EmptyCriterion'
]


class MySQLEngine(MySQLQuery):
    @overload
    def __init__(
            self,
            *,
            ip: str = ...,
            host: str = ...,
            port: int = ...,
            user: str = ...,
            username: str = ...,
            password: str = ...,
            database: str = ...,
    ) -> None: ...

    @overload
    def execute(self, sql: Text, commit: bool = ..., debug: bool = ...) -> QueryResult: ...

    @overload
    def commit(self): ...


class QueryResult:
    @overload
    def fetchone(self) -> Dict[str, Any]: ...

    @overload
    def fetchone(self, first: bool = ...) -> Any:
        """
        :param first: Whether to only fetch the value of the first field in the result
        """

    @overload
    def fetchmany(self, num: int) -> List[Dict[str, Any]]: ...

    @overload
    def fetchall(self) -> List[Dict[str, Any]]: ...

    @overload
    def fetchall(self, flat: bool = ...) -> list:
        """
        :param flat: Where to flatten the output
        """

