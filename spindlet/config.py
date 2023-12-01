import re

from pydantic import Field
from pydantic.v1 import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.spindlet', env_file_encoding='UTF-8')
    # Lib
    LIB_BIZ_NAME_PATTERN: re.Pattern = Field(re.compile(r'^([A-Z]+|Biz)Library$'),
                                             description='business library naming conventions')
    LIB_KW_NAME_PATTERN: re.Pattern = Field(re.compile(r'^Lib([A-Z][a-z]+)+$'),
                                            description='keyword library naming conventions for business action')
    LIB_KW_NAME_API_PATTERN: re.Pattern = Field(re.compile(r'^Api([A-Z][a-z]+)+$'),
                                                description='keyword library naming conventions for api request')
    LIB_KW_NAME_MOCK_PATTERN: re.Pattern = Field(re.compile(r'^Mock([A-Z][a-z]+)+$'),
                                                 description='keyword library naming conventions for mock setting')
    LIB_BASE_NAME_PATTEN: re.Pattern = Field(re.compile(r'^[A-Z]*BizBase$'),
                                             description='naming conventions for keyword base classes')
    LIB_NAME_PATTERNS: list = Field([
        LIB_BIZ_NAME_PATTERN, LIB_KW_NAME_PATTERN,
        LIB_BASE_NAME_PATTEN, LIB_KW_NAME_API_PATTERN, LIB_KW_NAME_MOCK_PATTERN
    ], description='library naming conventions set')
    # Keyword
    KW_CHECK_DOC: bool = Field(True, description='whether or not to check the keyword document')
    KW_ALLOW_PREFIX: tuple = Field(('send_', 'set_mock_'), description='non-keyword method prefix')
    # Context Variable
    CTX_VAR_VAL_PATTERN: re.Pattern = Field(re.compile(r'^\${([\w.]+)(\.\w+\(\))?}$'),
                                            description='the content in parentheses is identified as a '
                                                        'chained context variable and its built-in handling '
                                                        'method, respectively')
    CTX_VAR_NAME_PREFIX: str = Field('v_',
                                     description='prefix used to identify the parameter that '
                                                 'receives the context variable name')


settings = Settings()
print(settings.LIB_BASE_NAME_PATTEN.match('a'))
