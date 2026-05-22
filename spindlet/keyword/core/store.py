import copy

from spindlet.config import settings
from spindlet.keyword.core.exceptions import CtxVarError
from spindlet.utils import extract_value


def parser_ctx(val, ctx_vars: dict):
    """Parse keyword variables in arguments."""
    if isinstance(val, dict):
        return {n: parser_ctx(v, ctx_vars) for n, v in val.items()}
    elif isinstance(val, (tuple, list)):
        return [parser_ctx(v, ctx_vars) for v in val]
    elif isinstance(val, str):
        match = settings.CTX_VAR_PATTERN.match(val)
        if match:
            val = match.group(1)
            root = val.split(".", 1)[0]
            if root not in ctx_vars:
                raise CtxVarError(f"Keyword variable <{val}> does not exist in {ctx_vars}; set it first.")
            val = extract_value(ctx_vars, val, func=match.group(2))
    return val


class KeywordStore:
    """Keyword variable store shared across keyword methods."""

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
        """Save a keyword variable."""
        if name is None:
            return
        else:
            if not (isinstance(name, str) and name.isidentifier()):
                raise CtxVarError("Keyword variable name must be a string and a valid Python identifier.")
            elif not (value is None or isinstance(value, (int, float, bool, str, list, tuple, dict))):
                raise CtxVarError("Keyword variable value only supports: None, int, float, bool, str, list, tuple, dict.")
            else:
                self.__variables[name] = value

    def load(self, var: dict = None, lock: dict = None) -> None:
        if var is None:
            self.__variables = dict()
        else:
            self.__variables.update(var)
        self.__locked = lock or dict()

    def dump(self) -> dict:
        return dict(variables=copy.deepcopy(self.variables), locked=copy.deepcopy(self.locked))
