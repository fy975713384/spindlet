import sys
import traceback

import pendulum

from spindlet.keyword.runner.context import Context
from spindlet.keyword.runner.flow import FlowStateEnum


class _Runner:
    """ 关键字执行器基类 """

    # 控制 with 结束时是否需要抛出异常
    RAISE_EXCEPTION = True

    def __init__(self, flow, logger=None):
        self.flow = flow
        self.logger = logger

    @property
    def name(self):
        raise NotImplemented

    def begin(self):
        """ 执行器开始前动作 """
        self.logger.info(f"{self.name} Begin run...")
        self.flow.state = FlowStateEnum.FLOW_RUNNING
        self.flow.start_time = pendulum.now().format('HH:mm:ss')

    def end(self):
        """ 执行器结束时动作 """
        self.flow.end_time = pendulum.now().format('HH:mm:ss')
        self.logger.info(f"{self.name} Finished!")

    def success(self):
        """ 执行器执行成功时动作 """
        self.flow.state = FlowStateEnum.FLOW_SUCCESS
        self.logger.info(f"{self.name} Run success")

    def failure(self, exc_type, exc_val, exc_tb):
        """ 执行器执行失败时动作 """
        self.logger.error(f"{self.name} Run failure")
        self.flow.state = FlowStateEnum.FLOW_FAILURE

    def is_cancel(self):
        pass

    def run(self):
        raise NotImplemented

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == KeyboardInterrupt:
            return False
        if exc_type:
            if exc_type is AssertionError:
                exc_tb = exc_val if bool(str(exc_val).strip()) else "AssertionError"
            else:
                exc_tb = traceback.format_exc()
            self.failure(exc_type, exc_val, exc_tb)
        else:
            self.success()
        self.end()
        return not self.RAISE_EXCEPTION


class RunnerCtx(_Runner):
    """ 关键字执行上下文处理器 """

    def __init__(self, flow, logger, context):
        super().__init__(flow, logger)
        self.context = Context()
        self.context.load(context)

    def run_runner(self, runner, flow, context=None):
        with runner(flow=flow, logger=self.logger, context=context or self.context.dump()) as r:
            r.run()

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)


class StepRunner(RunnerCtx):
    """ 关键字执行器 """

    @property
    def name(self):
        return f"[STEP: {self.flow.func_name}]"

    @property
    def args(self):
        return self.flow.args

    def failure(self, exc_type, exc_val, exc_tb):
        super(StepRunner, self).failure(exc_type, exc_val, exc_tb)
        if exc_type is AssertionError:
            sys.tracebacklimit = 1
        self.context.logger.exception(exc_tb)

    def run(self):
        self.context.logger = self.context.logger.bind(keyword=self.flow.func_name)
        if self.context.instance:
            self.context.instance.logger = self.context.logger
        self.context.exec_func(self.flow.func_name, self.flow.args)
