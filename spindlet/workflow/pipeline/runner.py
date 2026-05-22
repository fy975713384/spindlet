from spindlet.keyword.runner.runner import RunnerCtx, StepRunner


class PipelineRunner(RunnerCtx):
    """
    线性关键字执行器，按顺序执行步骤列表
    """
    RAISE_EXCEPTION = True

    @property
    def name(self):
        return "Pipeline Task"

    @property
    def args(self):
        return self.flow.args

    @property
    def steps(self):
        return self.flow.steps

    def run(self):
        self.context.get_instance()
        self.context.variables.update(self.args)
        for step in self.steps:
            self.run_runner(runner=StepRunner, flow=step)