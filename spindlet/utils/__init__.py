from jsonpath_rw import parse


def extract_value(context: dict, pattern: str):
    try:
        p = parse(pattern)
    except Exception as e:
        raise ValueError(f"pattern is not a valid jsonpath expression：{e.args[0]}")
    match = p.find(context)
    if match:
        return match[0].value if len(match) == 1 else [_.value for _ in match]
    else:
        raise ValueError(f"fetch value error，please check if <{pattern}> exists in {context}")


class MethodGen:
    def __init__(self, trigger_method, method_name):
        self.__trigger_method = trigger_method
        self.__method_name = method_name

    def __getattr__(self, method_name):
        return MethodGen(self.__trigger_method, f"{self.__method_name}.{method_name}")

    def __call__(self, *args, **kwargs):
        return self.__trigger_method(self.__method_name, args, kwargs)
