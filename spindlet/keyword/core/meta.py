from spindlet.keyword.core.exceptions import KeywordLibraryDuplicateError
from spindlet.keyword.core.utils import is_keyword_method, reset_func_attribute, validate_keyword_method, validate_library_name


class KeywordMeta(type):
    _constructing_cls = None

    def __new__(mcs, name, bases, attrs):
        ori = type.__new__(mcs, name, bases, attrs)

        if name != 'KeywordBase':
            validate_library_name(name)
            for func_name, func in attrs.items():
                if is_keyword_method(func_name, func):
                    validate_keyword_method(name, func_name, func)
                    setattr(ori, func_name, reset_func_attribute(func))
        return ori

    def __call__(cls, *args, **kwargs):
        """Prevent nested keyword library instantiation."""
        if KeywordMeta._constructing_cls is not None:
            raise KeywordLibraryDuplicateError(
                f"Keyword library <{KeywordMeta._constructing_cls.__name__}> is being instantiated; "
                f"nested keyword library instantiation is not allowed: <{cls.__name__}>"
            )
        KeywordMeta._constructing_cls = cls
        try:
            return type.__call__(cls, *args, **kwargs)
        finally:
            KeywordMeta._constructing_cls = None
