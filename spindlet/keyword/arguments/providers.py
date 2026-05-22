from typing import Any, Protocol


class DataFactoryProvider(Protocol):
    def get_data(self, key: str, *, ctx: Any) -> Any:
        ...


class DataDictProvider(Protocol):
    def get_value(self, key: str, *, ctx: Any) -> Any:
        ...


class FunctionProvider(Protocol):
    def call(self, name: str, args: list[Any], *, ctx: Any) -> Any:
        ...
