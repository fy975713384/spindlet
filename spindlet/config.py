import re

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.spindlet', env_file_encoding='UTF-8')

    # Lib
    LIB_BIZ_NAME_PATTERN: re.Pattern = Field(re.compile(r'^([A-Z]+|Biz)Library$'), description='业务库命名规则')
    LIB_KW_NAME_PATTERN: re.Pattern = Field(re.compile(r'^Lib([A-Za-z0-9]+)+$'), description='关键字库命名规则')
    LIB_KW_NAME_API_PATTERN: re.Pattern = Field(re.compile(r'^Api([A-Za-z0-9]+)+$'), description='接口关键字库命名规则')
    LIB_KW_NAME_MOCK_PATTERN: re.Pattern = Field(re.compile(r'^Mock([A-Za-z0-9]+)+$'), description='Mock关键字库命名规则')
    LIB_BASE_NAME_PATTEN: re.Pattern = Field(re.compile(r'^[A-Z]*BizBase$'), description='关键字基类命名规则')
    LIB_NAME_PATTERNS: list = Field([
        LIB_BIZ_NAME_PATTERN, LIB_KW_NAME_PATTERN,
        LIB_BASE_NAME_PATTEN, LIB_KW_NAME_API_PATTERN, LIB_KW_NAME_MOCK_PATTERN
    ], description='库命名格式')
    # Keyword
    KW_CHECK_DOC: bool = Field(True, description='是否检查关键字文档')
    KW_NOT_STARTS: tuple = Field(('send_', 'set_mock_'), description='非关键字方法前缀')
    # Context Variable
    CTX_VAR_PATTERN: re.Pattern = Field(re.compile(r'^\${([A-z_]+[\w\.\[\]:\*]+)(\.\w+\(\))?}$'),
                                        description='圆括号中的内容将分别识别为链式的 context variable 及其内置处理方法')
    CTX_VAR_PREFIX: str = Field('v_', description='用于标识接收 context variable 名称的形参的前缀')
    # 增强参数：DF-数据工厂取数 DD-数据字典取值 FN-内置函数
    ENHANCE_VAR_TEMPLATE: re.Pattern = Field(re.compile(r'^\${((DF|DD|FN)\.)?([\w\.\[\]:\*]+)(\.\w+\((.*)\))?}$'),
                                             description='增强参数模板，支持 DF/DD/FN 前缀')


settings = Settings()
