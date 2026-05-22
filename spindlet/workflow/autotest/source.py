import copy
import importlib
from pathlib import Path
from typing import Dict, Literal, Any, List, Optional

from spindlet.keyword.runner.flow import FlowStateEnum
from spindlet.keyword.runner.source import Source, StepSource
from .runner import SuiteRunner
from .suite import SuiteAttributeError, CaseAttributeError, SuiteBase
from spindlet.utils.logger import sprint, white, red, green, yellow, blue


class SourceParseError(Exception):
    pass


class _FileSource(Source):
    """
    测试套件文件定义器
    """

    def __init__(self, source):
        super(_FileSource, self).__init__()
        self.source = None
        self.path = Path(source)
        # 考虑到导入 self.package 时，传入的 self.path 可能是相对路径，需要去除相对路径 ..
        self.package = ".".join([p for p in self.path.parts[:-1] if p != ".."] + [self.path.stem])


class LocalSuiteSource(_FileSource):
    """
    测试套件定义器
    """

    def __init__(self, source):
        super(LocalSuiteSource, self).__init__(source)
        self.module_id = None
        self.suite_id = None
        self.suite_name = None
        self.suite_args = None
        self.suite_setup = None
        self.case_setup = None
        self.case_wait = None
        self.case_main = None
        self.case_teardown = None
        self.suite_teardown = None

        self.concurrent = 1

        self.suite_options = None
        self.case_gatherer = []

        # 测试执行数据
        self.total = self.passed = self.failed = self.blocked = 0

    @property
    def name(self):
        return self.path.stem

    @property
    def cases(self):
        return self.case_gatherer

    @property
    def setup(self):
        return self.suite_setup

    @property
    def teardown(self):
        return self.suite_teardown

    def count(self, option, add_num):
        setattr(self, option, getattr(self, option) + add_num)

    def fetch_data_template(self, sign, cases=None, tags=None) -> List[Optional[dict]]:
        """ 获取数据模板，子类可重写以对接外部平台 """
        raise NotImplementedError("请重写 fetch_data_template 方法以支持数据模板获取")

    def __filling_cases(self, cases, levels, tags):
        """ 按需设置待执行的测试用例列表 """

        def __check_args(c):
            # 检查用例参数是否完整
            suite_args = set(self.suite_args.keys())
            case_args = set(c.get("args", {}).keys())
            for arg in self.suite_options.get("params"):
                if arg["name"] not in {*suite_args, *case_args}:
                    raise CaseAttributeError(f'用例<{_case.get("name")}>缺少参数：{arg}')

        if cases is None:
            pass
        elif isinstance(cases, (tuple, list, set)):
            # cid转换成字符串
            cases = [str(i) for i in cases]
        else:
            cases = (str(cases),)

        if template_sign := self.suite_options.get("case_template"):
            _cases: List[Optional[dict]] = self.fetch_data_template(sign=template_sign, cases=cases, tags=tags)
            if not _cases:
                raise CaseAttributeError(f"用例模版<{template_sign}>中不存在对应ID的测试用例：{cases}")
            for _case in _cases:
                __check_args(_case)
                _case["cid"] = _case.pop("id")
                self.case_gatherer.append(CaseSource(self, **_case))
        else:
            if not (_cases := self.suite_options.get("cases")):
                raise SuiteAttributeError(f"测试套件中未添加有效的测试用例数据")
            for _case in _cases:
                __check_args(_case)
                case = CaseSource(self, **_case)
                case = case and case.filter(cases=cases, levels=levels, tags=tags)
                if case:
                    self.case_gatherer.append(case)
            if not self.case_gatherer:
                raise CaseAttributeError(f"测试套件中不存在对应ID的测试用例：{cases}")

    def filling(self, cases=None, levels=None, tags=None, concurrent=1, **kwargs):
        module = importlib.import_module(self.package)
        suite_cls = getattr(module, "TestSuite", None)
        if suite_cls:
            suite: SuiteBase = suite_cls()
            self.suite_options = copy.deepcopy(suite.serialize())
            self.module_id = self.suite_options.get("module_id")
            self.suite_id = self.suite_options.get("sid")
            self.suite_name = self.suite_options.get("name")
            self.suite_args = self.suite_options.get("suite_args", {})
            self.suite_setup = StageSource(**self.suite_options.get("suite_setup"))
            self.case_setup = StageSource(**self.suite_options.get("case_setup"))
            self.case_wait = StageSource(**self.suite_options.get("case_wait"))
            self.case_main = StageSource(**self.suite_options.get("case_main"))
            self.case_teardown = StageSource(**self.suite_options.get("case_teardown"))
            self.suite_teardown = StageSource(**self.suite_options.get("suite_teardown"))
            self.__filling_cases(cases, levels, tags)
            self.concurrent = concurrent
            self.count("total", len(self.case_gatherer))
            return self
        else:
            raise SourceParseError(f"测试套件文件<{self.path}>中"
                                   f"未找到继承于<class SuiteBase>的测试套件类<class TestSuite>")

    def serialize(self) -> dict:
        return self.suite_options

    def run(self, env=None, token=None, logger=None):
        if self.case_wait.steps and self.concurrent < len(self.cases):
            raise SourceParseError(f"测试套件中使用 case_wait 时，执行并发数不能小于用例数")
        context = dict(env=env, logger=logger, token=token, library=self.suite_options.get("library"))
        with SuiteRunner(flow=self, logger=logger, context=context) as runner:
            runner.run()

    def report(self):
        sprint(white("=" * 100))
        sprint(white(f"[Suite] {self.package} <{self.start_time}> <{self.end_time}>    P/F/B/T: "
                     f"{green(self.passed, False)}/"
                     f"{red(self.failed, False)}/"
                     f"{yellow(self.blocked, False)}/"
                     f"{blue(self.total, False)}"))
        for case in self.case_gatherer:
            case.report()

    def summary(self):
        sprint(white("=" * 100))
        sprint(white(f"测试完成, 本次测试共「{blue(self.total, nl=False)}」个用例, 其中 "
                     f"「{green(self.passed, nl=False)}」成功,"
                     f"「{red(self.failed, nl=False)}」失败,"
                     f"「{yellow(self.blocked, nl=False)}」阻塞"))


class FormatSuiteSource(Source):
    def __init__(self, *, name, library,
                 suite_args, suite_setup, case_setup, case_wait, case_main, case_teardown, suite_teardown,
                 cases: List[Dict[Literal["id", "name", "args"], Any]],
                 is_concurrent: bool = True):
        super(FormatSuiteSource, self).__init__()
        # 测试统计数据
        self.total = self.passed = self.failed = self.blocked = 0
        # 测试执行数据
        self.suite_name = name
        self.library = library
        self.suite_args = suite_args
        self.suite_setup = StageSource(name="suite_setup", steps=suite_setup or [])
        self.case_setup = StageSource(name="case_setup", steps=case_setup or [])
        self.case_wait = StageSource(name="case_wait", steps=case_wait or [])
        self.case_main = StageSource(name="case_main", steps=case_main or [])
        self.case_teardown = StageSource(name="case_teardown", steps=case_teardown or [])
        self.suite_teardown = StageSource(name="suite_teardown", steps=suite_teardown or [])
        self.case_gatherer: List[CaseSource] = []
        if is_concurrent:
            if self.case_wait:
                self.concurrent = max(len(cases), 1)
            else:
                self.concurrent = (4 if len(cases) < 40 else 8)
        else:
            self.concurrent = 1
        # 测试初始化动作
        self.__filling_cases(cases)

    @property
    def name(self):
        return self.suite_name

    @property
    def cases(self):
        return self.case_gatherer

    @property
    def setup(self):
        return self.suite_setup

    @property
    def teardown(self):
        return self.suite_teardown

    def __filling_cases(self, cases):
        for case in cases:
            self.case_gatherer.append(
                CaseSource(self, cid=case.get("id"), name=case.get("name"), args=case.get("args")))
        self.count("total", len(self.case_gatherer))

    def count(self, option, add_num):
        setattr(self, option, getattr(self, option) + add_num)

    def run(self, token=None, env=None, logger=None):
        context = dict(token=token, env=env, logger=logger, library=self.library)
        with SuiteRunner(flow=self, logger=logger, context=context) as runner:
            runner.run()

    def serialize(self) -> dict:
        return dict(
            total=self.total,
            passed=self.passed,
            failed=self.failed,
            blocked=self.blocked,
            start_time=self.start_time,
            end_time=self.end_time,
            case_gatherer=[{
                "cid": _.cid, "name": _.name, "state": _.state.value, "err_log": _.err_log,
                "start_time": _.start_time, "end_time": _.end_time
            } for _ in self.case_gatherer]
        )


class CaseSource(Source):
    """
    测试用例定义器
    """

    def __init__(self, suite, cid=None, name: str = None, level: str = None, tags: List = None, args: dict = None):
        super(CaseSource, self).__init__()
        self.suite = suite
        self.cid = cid
        self.__name = name
        self.level = level
        self.tags = tags
        self.args = args
        self.err_log = None

    @property
    def name(self):
        return self.__name

    @property
    def setup(self):
        return self.suite.case_setup

    @property
    def blocker(self):
        return self.suite.case_wait

    @property
    def mainer(self):
        return self.suite.case_main

    @property
    def teardown(self):
        return self.suite.case_teardown

    def filter(self, cases=None, levels=None, tags=None):
        # 过滤掉未设置名称的用例
        if not any((self.name,)):
            return None
        # 过滤掉未指定执行的用例（--cases 指定执行的用例集）
        if cases:
            if str(self.cid) not in cases:
                return None
        # 过滤掉未指定级别的用例（--levels 执行执行的标签）
        if levels:
            if self.level not in levels:
                return None
        # 过滤掉未指定标签的用例（--tags 执行执行的标签）
        if tags:
            if set(self.tags or []).isdisjoint(set(tags)):
                return None
        return self

    def report(self):
        state = {
            FlowStateEnum.FLOW_SUCCESS: green("SUCCESS", nl=False),
            FlowStateEnum.FLOW_FAILURE: red("FAILURE", nl=False),
            FlowStateEnum.FLOW_BLOCKING: yellow("BLOCKING", nl=False)
        }.get(self.state)

        sprint(white("-" * 100))
        sprint(white(f"[Case] <{self.cid}> {self.name} <{self.start_time}> <{self.end_time}>    |{state}|"))
        if self.state in [FlowStateEnum.FLOW_FAILURE, FlowStateEnum.FLOW_BLOCKING]:
            if self.err_log:
                sprint(red(self.err_log))


class StageSource(Source):
    """
    测试阶段定义器
    """

    def __init__(self, name, steps: List[Dict[Literal["func_name", "args"], Any]]):
        super(StageSource, self).__init__()
        self.__name = name
        self.steps = [StepSource(**step) for step in steps]

    @property
    def name(self):
        return self.__name


def render_source(source: str, **kwargs) -> LocalSuiteSource:
    if Path(source).exists():
        if source.endswith(".py"):
            source = LocalSuiteSource(source)
            return source.filling(**kwargs)
        else:
            raise SourceParseError("测试套件文件必须是以 .py 结尾的 python 文件")
    else:
        raise FileExistsError(f"测试套件集或测试套件<{source}>不存在")
