import functools
import inspect

from spindlet.config import settings
from spindlet.keyword.core.exceptions import (
    KeywordLibraryError,
    KeywordNameError,
    KeywordNoDocError,
    KeywordValueError,
)
from spindlet.keyword.core.store import parser_ctx


def is_keyword_method(func_name, func):
    """Return whether a class attribute should be treated as a keyword method."""
    return (
            inspect.isroutine(func)
            and not func_name.startswith('_')
            and not isinstance(func, (property, functools.cached_property))
    )


def validate_library_name(name):
    """Validate the keyword library naming convention."""
    if not any(_.default.match(name) for _ in settings.LIB_NAME_PATTERNS):
        raise KeywordLibraryError(f"Keyword library <{name}> does not match the naming convention.")


def validate_keyword_method(library_name, func_name, func):
    validate_keyword_doc(library_name, func_name, func)
    validate_keyword_name(library_name, func_name)
    validate_keyword_store_params(library_name, func_name, func)


def validate_keyword_doc(library_name, func_name, func):
    """Validate that keyword methods have documentation."""
    if settings.KW_CHECK_DOC and not func.__doc__ and not any(
            func_name.startswith(prefix) for prefix in settings.KW_NOT_STARTS
    ):
        raise KeywordNoDocError(f"Keyword method <{library_name}.{func_name}> must have a docstring.")


def validate_keyword_name(library_name, func_name):
    """Validate the keyword method naming convention."""
    if not func_name.islower():
        raise KeywordNameError(f"Keyword method <{func_name}> does not match the naming convention.")
    # Framework constraint: keyword methods in a LibXxx library must start with the library semantic prefix.
    if settings.LIB_KW_NAME_PATTERN.match(library_name) and func_name.split("_")[0] not in library_name.lower():
        raise KeywordNameError(f"Keyword method <{func_name}> does not match the naming convention.")


def validate_keyword_store_params(library_name, func_name, func):
    """Validate that keyword variable receiver parameters default to None."""
    for param_name, param in inspect.signature(func).parameters.items():
        if param_name.startswith(settings.CTX_VAR_PREFIX) and param.default is not None:
            raise KeywordValueError(
                f"Keyword variable parameter <{param_name}> in method <{library_name}.{func_name}> "
                f"must default to None."
            )


def reset_func_attribute(func):
    """Reset keyword method arguments — wraps the function to resolve context variables at call time."""

    @functools.wraps(func)
    def parser_attr(self, *args, **kwargs):
        args = parser_ctx(args, self.store.variables)
        kwargs = {name: parser_ctx(value, self.store.variables) for name, value in kwargs.items()}
        return func(self, *args, **kwargs)

    return parser_attr
