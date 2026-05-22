import json
from json import JSONDecodeError

from jsonpath_ng import parse

from .command import Cmd


def extract_value(context: dict, pattern: str, func: str = None, arg: str = None):
    """ 从字典中按模式取值 """
    try:
        p = parse(pattern)
    except Exception as e:
        raise ValueError(f"取值表达式错误：{e.args[0]}")
    match = p.find(context)
    if match:
        origin_data = match[0].value if len(match) == 1 else [_.value for _ in match]
        if func == ".json()":
            if origin_data in (None, ''):
                return origin_data
            try:
                return json.loads(origin_data)
            except JSONDecodeError:
                raise ValueError(f"取值错误，{origin_data} 不是有效的 JSON 字符串，不可使用 .json() 方法")
        elif func == ".str()":
            return str(origin_data)
        else:
            return origin_data
    else:
        raise ValueError(f"取值错误，请检查 {context} 是否存在 {pattern}")


class MethodGen:
    """ 生成链式调用方法 """

    def __init__(self, trigger_method, method_name):
        self.__trigger_method = trigger_method
        self.__method_name = method_name

    def __getattr__(self, method_name):
        return MethodGen(self.__trigger_method, f"{self.__method_name}.{method_name}")

    def __call__(self, *args, **kwargs):
        return self.__trigger_method(self.__method_name, args, kwargs)
