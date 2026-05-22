import ast
import inspect
import textwrap
from typing import List, Dict, Literal, Any, Type, Optional

from spindlet.config import settings
from spindlet.keyword.core import KeywordBase
from spindlet.utils import MethodGen


class SuiteAttributeError(Exception):
    pass


class CaseAttributeError(Exception):
    pass


class _Stage:
    """ 自动化测试阶段预处理器 """

    def __init__(self, stage_func):
        self.__stage = stage_func
        self.__steps: List[Dict[Literal["func_name", "args"], Any]] = []

    def add_step(self, func_name, args, kwargs):
        if args:
            raise SuiteAttributeError(f"禁止使用位置参数调用关键字方法<{func_name}>")
        self.__steps.append({"func_name": func_name, "args": kwargs})

    def get_stage_args(self) -> list:
        return [step.get("args") for step in self.__steps]

    def serialize(self) -> dict:
        return dict(name=self.__stage.__name__, steps=self.__steps)


class SuiteBase:
    """ 自动化测试套件解析器 """
    # 依赖的业务库
    LIBRARY: Optional[Type] = None
    # 业务模块ID
    MODULE_ID: Optional[int] = None
    # 测试套件ID
    SUITE_ID: Optional[int] = None
    # 测试套件名称, 应唯一
    SUITE_NAME: Optional[str] = None
    # 测试套件描述
    SUITE_DESC: Optional[str] = None
    # 套件参数，套件执行期间仅初始化一次，全部用例共用
    SUITE_ARGS: Dict[str, Any] = {}
    # 套件所属组别
    SUITE_GROUP: Optional[Literal["SIT", "UAT", "DEV"]] = None
    # 数据模板标识，测试套件依赖的数据模板
    CASE_TEMPLATE: Optional[str] = None
    # 测试用例集合
    CASES: List[Dict[Literal["cid", "name", "level", "tags", "args"], Any]] = []
    # 测试用例参数描述
    CASE_ARGS_DESC: Dict[str, str] = {}

    def suite_setup(self) -> None:
        """ 自动化测试套件前置钩子 """
        pass

    def case_setup(self) -> None:
        """ 自动化测试用例前置钩子 """
        pass

    def case_wait(self) -> None:
        """ 自动化测试用例执行等待器 """
        pass

    def case_main(self) -> None:
        """ 自动化测试用例执行器 """
        pass

    def case_teardown(self) -> None:
        """ 自动化测试用例后置钩子 """
        pass

    def suite_teardown(self) -> None:
        """ 自动化测试套件后置钩子 """
        pass

    def __init__(self):
        self.__stage = None
        self.__params: List[Dict[Literal["name", "description"], str]] = []  # 套件依赖形参
        self.__ctx_var: List[str] = []  # 套件内部关键字变量

    def __getattr__(self, name):
        return MethodGen(self.__stage.add_step, name)

    def __fill_stage(self, stage_func) -> dict:
        """ 填充 stage 内容 """
        for _ in ast.parse(textwrap.dedent(inspect.getsource(stage_func))).body[0].body:  # noqa
            if isinstance(_, ast.Pass):
                continue
            elif isinstance(_, ast.Expr) and isinstance(_.value, ast.Constant) and isinstance(_.value.value, str):
                continue
            elif isinstance(_, ast.Expr) and isinstance(_.value, ast.Call) and isinstance(_.value.func, ast.Attribute):
                continue
            else:
                raise SuiteAttributeError(f"套件方法中仅支持调用关键字方法，不支持使用其他表达式：{ast.dump(_)}")
        self.__stage = _Stage(stage_func)
        # 调用钩子或执行器方法，执行关键字方法时触发 __getattr__，将所需执行的关键字填充进 stage
        stage_func()
        self.__parse_suite_params(self.__stage.get_stage_args())
        return self.__stage.serialize()

    def __parse_case_ctx_args(self, stage_params: list):
        """ 解析用例参数中关键字变量名 """
        self.__ctx_var.extend(stage_params)

    def __parse_suite_params(self, args: List[dict]):
        """ 解析套件依赖形参 """
        for kw in args:
            for k, v in kw.items():
                if k.startswith("v_") and v and isinstance(v, str):
                    self.__ctx_var.append(v)
                if isinstance(v, str) and (match := settings.CTX_VAR_PATTERN.match(v)):
                    name = match.group(1)
                    # 判断非增强型上下文取值语法
                    if "." in name:
                        raise SuiteAttributeError(f"套件中配置的关键字实参不允许通过 `.` 方式进行链式取值：{v}")
                    elif name in self.__ctx_var:
                        pass
                    elif name in (_.get("name") for _ in self.__params):
                        pass
                    else:
                        _des = self.CASE_ARGS_DESC.get(name) if name in self.CASE_ARGS_DESC else ""
                        self.__params.append({"name": name, "description": _des})

    def serialize(self):
        """ 序列化自动化测试套件信息 """
        # 检查套件属性
        if self.LIBRARY is None or not issubclass(self.LIBRARY, KeywordBase):
            raise SuiteAttributeError(f"不正确的业务测试关键字库类：{str(self.LIBRARY)}")
        if not self.SUITE_NAME or not self.SUITE_DESC:
            raise SuiteAttributeError(f"未设置自动化测试套件名称或描述")
        if self.SUITE_ARGS and not isinstance(self.SUITE_ARGS, dict):
            raise SuiteAttributeError(f"SUITE_ARGS 格式错误")
        if self.CASE_TEMPLATE and self.CASES:
            raise SuiteAttributeError(f"CASE_TEMPLATE 和 CASES 只能设置其一")
        if not isinstance(self.CASES, list):
            raise SuiteAttributeError(f"CASES 必须为列表类型")
        else:
            for case in self.CASES:
                if not {"cid", "name", "args"}.issubset(case):
                    raise CaseAttributeError(f"用例中缺少<cid|name|args>参数，请检查")

        return dict(
            library=self.LIBRARY,
            sid=self.SUITE_ID,
            name=self.SUITE_NAME,
            description=self.SUITE_DESC,
            module_id=self.MODULE_ID,
            suite_args=self.SUITE_ARGS,
            suite_group=self.SUITE_GROUP,
            case_template=self.CASE_TEMPLATE,
            cases=self.CASES,
            suite_setup=self.__fill_stage(self.suite_setup),
            case_setup=self.__fill_stage(self.case_setup),
            case_wait=self.__fill_stage(self.case_wait),
            case_main=self.__fill_stage(self.case_main),
            case_teardown=self.__fill_stage(self.case_teardown),
            suite_teardown=self.__fill_stage(self.suite_teardown),
            params=self.__params,  # 必须置于最后（需等待所有stage都填充完成）
        )
