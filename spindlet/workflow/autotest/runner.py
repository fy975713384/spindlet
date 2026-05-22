import copy
import time
import traceback
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List
import threading
import pendulum

from spindlet.keyword.runner.flow import FlowStateEnum
from spindlet.keyword.runner.runner import RunnerCtx, StepRunner
from spindlet.keyword.runner.source import Source

lock = threading.Lock()
case_wait_state = False
case_setup_sign = 0


class SuiteRunner(RunnerCtx):
    """Test suite runner."""

    RAISE_EXCEPTION = False

    def __init__(self, *args, **kwargs):
        super(SuiteRunner, self).__init__(*args, **kwargs)
        self.case_run = False

    @property
    def name(self):
        return f"[SUITE: {self.flow.name}]"

    @property
    def cases(self):
        return self.flow.cases

    def failure(self, exc_type, exc_val, exc_tb):
        """Handle suite run failure."""
        super(SuiteRunner, self).failure(exc_type, exc_val, exc_tb)
        if not self.case_run:
            self.flow.count("blocked", self.flow.total)
            for case in self.cases:
                case.state = FlowStateEnum.FLOW_BLOCKING
                case.start_time = case.start_time or pendulum.now().format('HH:mm:ss')
                case.end_time = case.end_time or pendulum.now().format('HH:mm:ss')
                case.err_log = f"[ERROR: suite_setup]: {exc_val}"

    def run(self):
        # Initialize suite arguments once for the suite session.
        self.context.variables.update(self.context.parse_args(self.flow.suite_args) or {})
        # Initialize the shared keyword library instance before suite execution.
        self.context.get_instance()
        try:
            self.run_runner(runner=StageRunner, flow=self.flow.setup)
            self._run_cases()
        finally:
            self.run_runner(runner=StageRunner, flow=self.flow.teardown)

    def _run_cases(self):
        case_info: List[dict] = []
        for case in self.cases:
            # Keep keyword variables isolated between cases.
            ctx = self.context.dump()
            ctx["variables"] = copy.deepcopy(ctx["variables"])
            instance_store = self.context.instance.store.dump()
            ctx["instance"] = self.context.create_instance()
            ctx["instance"].store.load(var=instance_store["variables"], lock=instance_store["locked"])
            if isinstance(case.args, dict):
                ctx["variables"].update(case.args)
            case_info.append(dict(case=case, ctx=ctx))

        global case_wait_state, case_setup_sign
        case_wait_state = False
        case_setup_sign = len(case_info)
        self.case_run = True
        with ThreadPoolExecutor(max_workers=self.flow.concurrent) as executor:
            to_do = [executor.submit(self.run_runner, CaseRunner, _["case"], _["ctx"]) for _ in case_info]
            for future in as_completed(to_do):
                future.result()
        case_wait_state = False


class CaseRunner(RunnerCtx):
    """
    Test case runner.
    """
    RAISE_EXCEPTION = False

    def __init__(self, *args, **kwargs):
        super(CaseRunner, self).__init__(*args, **kwargs)
        self.case_run = False
        self.case_errors = []

    @property
    def name(self):
        return f"[CASE: {self.flow.name}]"

    def success(self):
        """Handle case run success."""
        super(CaseRunner, self).success()
        self.flow.suite.count("passed", 1)

    def failure(self, exc_type, exc_val, exc_tb):
        """Handle case run failure."""
        super(CaseRunner, self).failure(exc_type, exc_val, exc_tb)
        self.flow.err_log = "\n".join(self.case_errors)
        if (not self.case_run) or (exc_type is not AssertionError):
            self.flow.state = FlowStateEnum.FLOW_BLOCKING
            self.flow.suite.count("blocked", 1)
        else:
            self.flow.suite.count("failed", 1)

    def run_stage(self, stage: Source):
        if stage.name == "case_main":
            self.case_run = True
        try:
            self.run_runner(runner=StageRunner, flow=stage)
        except Exception:
            self.case_errors.append(f"[ERROR: {stage.name}]: {traceback.format_exc(0)}")
            raise

    def run(self):
        global case_wait_state, case_setup_sign
        self.context.logger = self.context.logger.bind(case_id=self.flow.cid)
        try:
            self.run_stage(self.flow.setup)
            case_setup_sign -= 1
            with lock:
                if self.flow.blocker.steps and not case_wait_state:
                    while case_setup_sign != 0:
                        time.sleep(0.7)
                    try:
                        self.run_stage(self.flow.blocker)
                    finally:
                        case_wait_state = True
            self.run_stage(self.flow.mainer)
        finally:
            self.run_stage(self.flow.teardown)


class StageRunner(RunnerCtx):
    """
    Test stage runner.
    """

    @property
    def name(self):
        return f"[STAGE: {self.flow.name}]"

    @property
    def steps(self):
        return self.flow.steps

    def run(self):
        for step in self.steps:
            self.run_runner(runner=StepRunner, flow=step)
