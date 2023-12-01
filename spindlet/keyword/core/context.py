import copy
import json

from spindlet.config import settings
from spindlet.utils import extract_value


class CtxVarError(Exception):
    pass


def parser_ctx(val, ctx_vars: dict):
    """ 解析实参中的 context variable """
    if isinstance(val, dict):
        return {n: parser_ctx(v, ctx_vars) for n, v in val.items()}
    elif isinstance(val, (tuple, list)):
        return [parser_ctx(v, ctx_vars) for v in val]
    elif isinstance(val, str):
        match = settings.CTX_VAR_PATTERN.match(val)
        if match:
            val = match.group(1)  # matched context variable
            root = val.split(".", 1)[0]
            if root not in ctx_vars:
                raise CtxVarError(f"context variable <{val}> not exists in {ctx_vars}, "
                                  f"please set it in the code first")
            val = extract_value(ctx_vars, val)
            if func := match.group(2):
                if func == ".json()":
                    val = json.loads(val)
    return val


class Context:
    def __init__(self):
        self.__variables = dict()
        self.__locked = dict()

    @property
    def variables(self):
        return self.__variables

    @property
    def locked(self):
        return self.__locked

    def save(self, name, value) -> None:
        """ 保存 context variable """
        if name is None:
            return
        else:
            if isinstance(name, str) and name.isidentifier():
                self.__variables[name] = value
            else:
                raise CtxVarError(f"the context variable name must be a string and a valid Python identifier")

    def load(self, var: dict = None, lock: dict = None) -> None:
        if var is None:
            self.__variables = dict()
        else:
            self.__variables.update(var)
        self.__locked = lock or dict()

    def dump(self) -> dict:
        return dict(variables=copy.deepcopy(self.variables), locked=copy.deepcopy(self.locked))
