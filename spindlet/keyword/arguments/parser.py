import json
import re
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Any, Mapping, Sequence

from .resolver import (
    ArgumentResolver,
    ContextVarResolver,
    DataDictResolver,
    DataFactoryResolver,
    FunctionResolver,
)


class ArgumentResolveError(ValueError):
    pass


@dataclass
class ArgumentResolveContext:
    token: Any = None
    env: Any = None
    logger: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    providers: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArgumentExpression:
    prefix: str | None
    body: str
    transforms: Sequence[str]


class ArgumentParser:
    _ARG_PATTERN = re.compile(r"^\${(.+)}$")
    _TRANSFORMS = (".json()", ".str()")

    def __init__(self, resolvers: Sequence[ArgumentResolver] | None = None):
        self.resolvers = list(resolvers or self.default_resolvers())

    @classmethod
    def default_resolvers(cls) -> list[ArgumentResolver]:
        return [
            DataFactoryResolver(),
            DataDictResolver(),
            FunctionResolver(),
            ContextVarResolver(),
        ]

    def parse(self, args: Any, ctx: ArgumentResolveContext) -> Any:
        if isinstance(args, dict):
            return {name: self.parse(value, ctx) for name, value in args.items()}
        if isinstance(args, list):
            return [self.parse(value, ctx) for value in args]
        if isinstance(args, tuple):
            return tuple(self.parse(value, ctx) for value in args)
        if isinstance(args, set):
            return {self.parse(value, ctx) for value in args}
        if isinstance(args, str):
            return self.parse_string(args, ctx)
        return args

    def parse_string(self, value: str, ctx: ArgumentResolveContext) -> Any:
        match = self._ARG_PATTERN.match(value)
        if not match:
            return value
        expression = self.parse_expression(match.group(1))
        resolver = self.get_resolver(expression)
        resolved = resolver.resolve(expression.body, ctx)
        return self.apply_transforms(resolved, expression.transforms)

    def parse_expression(self, raw_expression: str) -> ArgumentExpression:
        expression = raw_expression.strip()
        transforms = []
        while True:
            transform = next((item for item in self._TRANSFORMS if expression.endswith(item)), None)
            if transform is None:
                break
            transforms.insert(0, transform)
            expression = expression[: -len(transform)]

        prefix, body = self.split_prefix(expression)
        if not body:
            raise ArgumentResolveError(f"Argument expression is empty: {raw_expression}")
        return ArgumentExpression(prefix=prefix, body=body, transforms=transforms)

    @staticmethod
    def split_prefix(expression: str) -> tuple[str | None, str]:
        prefix, separator, body = expression.partition(".")
        if separator and prefix in {"DF", "DD", "FN"}:
            return prefix, body
        return None, expression

    def get_resolver(self, expression: ArgumentExpression) -> ArgumentResolver:
        for resolver in self.resolvers:
            if resolver.match(expression.prefix):
                return resolver
        prefix = expression.prefix or "context"
        raise ArgumentResolveError(f"Unsupported argument expression prefix: {prefix}")

    @staticmethod
    def apply_transforms(value: Any, transforms: Sequence[str]) -> Any:
        for transform in transforms:
            if transform == ".json()":
                if value in (None, ""):
                    continue
                try:
                    value = json.loads(value)
                except (JSONDecodeError, TypeError):
                    raise ArgumentResolveError(f"Value {value} is not a valid JSON string; .json() cannot be used.")
            elif transform == ".str()":
                value = str(value)
            else:
                raise ArgumentResolveError(f"Unsupported argument transform: {transform}")
        return value
