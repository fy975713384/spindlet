import copy
import importlib
from typing import Union, Optional

from spindlet.keyword.arguments import ArgumentParser, ArgumentResolveContext
from spindlet.keyword.core.base import KeywordBase


class Context:
    def __init__(self):
        self.token = None
        self.library = None
        self.env = None
        self.logger = None
        self.instance: Optional[KeywordBase] = None
        self.variables: dict = {}
        self.arg_providers: dict = {}
        self.arg_parser = ArgumentParser()

    def load(self, context: dict):
        for k, v in context.items():
            setattr(self, k, v)
        if self.instance:
            self.instance.store.load(self.variables)

    def dump(self) -> dict:
        return dict(
            token=self.token,
            library=self.library,
            env=self.env,
            logger=self.logger,
            instance=self.instance,
            variables=self.variables,
            arg_providers=self.arg_providers,
            arg_parser=self.arg_parser,
        )

    @classmethod
    def get_library_cls(cls, library: Union[str, type]) -> type:
        """
        Get the keyword library class.
        :param library: keyword library class or module path string, formatted as "module.path:ClassName"
        :return: keyword library class
        """
        if isinstance(library, type) and issubclass(library, KeywordBase):
            return library
        elif isinstance(library, str):
            module, cls_name = library.rsplit(":", 1)
            module = importlib.import_module(module)
            return getattr(module, cls_name)
        else:
            raise ValueError(f"Invalid keyword library: {library}")

    def create_instance(self) -> KeywordBase:
        library_cls = self.get_library_cls(self.library)
        instance = library_cls(env=self.env, logger=self.logger)
        instance.store.load(copy.deepcopy(self.variables))
        return instance

    def get_instance(self) -> KeywordBase:
        if not self.instance:
            self.instance = self.create_instance()
        else:
            self.instance.store.load(copy.deepcopy(self.variables))
        return self.instance

    def parse_args(self, args):
        """Parse keyword arguments, including keyword variables and pluggable enhanced arguments."""
        ctx = ArgumentResolveContext(
            token=self.token,
            env=self.env,
            logger=self.logger,
            variables=self.variables,
            providers=self.arg_providers,
        )
        return self.arg_parser.parse(args, ctx)

    def exec_func(self, func_name, args):
        args = self.parse_args(copy.deepcopy(args))
        self.logger.info(f"Execution arguments: {args}")
        instance = self.get_instance()
        func = getattr(instance, func_name)
        func(**args)
