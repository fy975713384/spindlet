class KeywordError(Exception):
    """Base error for keyword core failures."""


class KeywordDefinitionError(KeywordError):
    """Raised when a keyword library or keyword method definition is invalid."""


class KeywordLibraryError(KeywordDefinitionError):
    pass


class KeywordMethodError(KeywordDefinitionError):
    pass


class KeywordNoDocError(KeywordMethodError):
    pass


class KeywordNameError(KeywordMethodError):
    pass


class KeywordValueError(KeywordMethodError):
    pass


class KeywordLibraryDuplicateError(KeywordError):
    pass


class CtxVarError(KeywordError):
    pass
