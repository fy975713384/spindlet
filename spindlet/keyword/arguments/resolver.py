import ast
import inspect
from typing import Any, Protocol

from spindlet.utils import extract_value


class MissingArgumentProviderError(ValueError):
    pass


class ArgumentResolver(Protocol):
    def match(self, prefix: str | None) -> bool:
        ...

    def resolve(self, expression: str, ctx: Any) -> Any:
        ...


class ContextVarResolver:
    def match(self, prefix: str | None) -> bool:
        return prefix is None

    def resolve(self, expression: str, ctx: Any) -> Any:
        return extract_value(ctx.variables, expression)


class _ProviderResolver:
    prefix: str
    provider_methods: tuple[str, ...]

    def match(self, prefix: str | None) -> bool:
        return prefix == self.prefix

    def get_provider(self, ctx: Any) -> Any:
        provider = ctx.providers.get(self.prefix)
        if provider is None:
            raise MissingArgumentProviderError(f"Missing {self.prefix} argument provider; enhanced argument cannot be resolved.")
        return provider

    @staticmethod
    def call_provider(method: Any, *args: Any, ctx: Any) -> Any:
        signature = inspect.signature(method)
        parameters = signature.parameters.values()
        accepts_ctx = any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD or parameter.name == "ctx"
            for parameter in parameters
        )
        if accepts_ctx:
            return method(*args, ctx=ctx)
        return method(*args)

    def get_provider_method(self, provider: Any) -> Any:
        for method_name in self.provider_methods:
            method = getattr(provider, method_name, None)
            if method is not None:
                return method
        method_names = ", ".join(self.provider_methods)
        raise MissingArgumentProviderError(f"{self.prefix} argument provider is missing a callable method: {method_names}")


class DataFactoryResolver(_ProviderResolver):
    prefix = "DF"
    provider_methods = ("get_data", "resolve", "get")

    def resolve(self, expression: str, ctx: Any) -> Any:
        method = self.get_provider_method(self.get_provider(ctx))
        return self.call_provider(method, expression, ctx=ctx)


class DataDictResolver(_ProviderResolver):
    prefix = "DD"
    provider_methods = ("get_value", "resolve", "get")

    def resolve(self, expression: str, ctx: Any) -> Any:
        method = self.get_provider_method(self.get_provider(ctx))
        return self.call_provider(method, expression, ctx=ctx)


class FunctionResolver(_ProviderResolver):
    prefix = "FN"
    provider_methods = ("call", "resolve", "get")

    def resolve(self, expression: str, ctx: Any) -> Any:
        name, args = self.parse_call(expression)
        method = self.get_provider_method(self.get_provider(ctx))
        if method.__name__ == "call":
            return self.call_provider(method, name, args, ctx=ctx)
        return self.call_provider(method, expression, ctx=ctx)

    @staticmethod
    def parse_call(expression: str) -> tuple[str, list[Any]]:
        name, separator, raw_args = expression.partition("(")
        if not separator:
            return expression, []
        if not raw_args.endswith(")"):
            raise ValueError(f"Invalid function enhanced argument format: {expression}")
        raw_args = raw_args[:-1].strip()
        if not raw_args:
            return name, []
        try:
            args = ast.literal_eval(f"({raw_args},)")
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Function enhanced arguments only support Python literal arguments: {expression}") from exc
        return name, list(args)
