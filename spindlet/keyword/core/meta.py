import functools
import inspect

from spindlet.config import settings
from spindlet.keyword.core.context import parser_ctx


class KeywordNoDocError(Exception):
    pass


class KeywordNameError(Exception):
    pass


class KeywordValueError(Exception):
    pass


class KeywordLibraryError(Exception):
    pass


class KeywordLibraryDuplicateError(Exception):
    pass


class KeywordMeta(type):

    def __new__(mcs, name, bases, attrs):
        ori = type.__new__(mcs, name, bases, attrs)

        if name != 'KeywordBase':
            # verify the library naming convention
            if not any(_.default.match(name) for _ in settings.LIB_NAME_PATTERNS):
                raise KeywordLibraryError(f'the naming format for the keyword library <{name}> '
                                          f'dose not comply with the conventions, please correct it')
            for func_name, func in attrs.items():
                # determine whether the method is a keyword method
                if inspect.isroutine(func) and not func_name.startswith('_'):
                    if (not func_name.islower() or
                            settings.LIB_KW_NAME_PATTERN.match(name) and
                            not func_name.split('_')[0] in name.lower()):
                        raise KeywordNameError(f'the naming format for the keyword method <{func_name}>'
                                               f'dose not comply with the conventions, please correct it')
                    if settings.KW_CHECK_DOC and not func.__doc__ and \
                            not any(func_name.startswith(_) for _ in settings.KW_ALLOW_PREFIX):
                        raise KeywordNoDocError(f'keyword method <{name}.{func_name}> '
                                                f'lacks documentation strings, please add')

                    # control business keyword context variable parameter must default to None
                    if sign := inspect.signature(func):
                        for k, v in sign.parameters.items():
                            if k.startswith(settings.CTX_VAR_PREFIX) and v.default is not None:
                                raise KeywordValueError(f'the default value for the context variable <{k}> '
                                                        f'in the keyword method <{name}.{func_name}> must be '
                                                        f'set to None')

                    # parse the context variables contained in the arguments
                    setattr(ori, func_name, reset_func_attribute(func))
        return ori

    def __call__(cls, *args, **kwargs):
        if not hasattr(KeywordMeta, 'instance'):
            __instance = type.__call__(cls, *args, **kwargs)
            KeywordMeta.instance = __instance
            return __instance
        elif (not issubclass(new_cls := KeywordMeta.instance.__class__, cls)) or (new_cls.__name__ == cls.__name__):
            return type.__call__(cls, *args, **kwargs)
        else:
            raise KeywordLibraryDuplicateError(
                f'The keyword library cannot be instantiated multiple times：{cls.__name__}')


def reset_func_attribute(func):
    @functools.wraps(func)
    def parser_attr(self, *args, **kwargs):
        args = parser_ctx(args, self.ctx.variables)
        for n, v in kwargs.items():
            kwargs.update({n: parser_ctx(v, self.ctx.variables)})
        return func(self, *args, **kwargs)

    return parser_attr
