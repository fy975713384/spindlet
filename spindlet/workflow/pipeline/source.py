from typing import List, Dict, Literal, Union

from spindlet.keyword.runner.source import Source, StepSource
from spindlet.workflow.pipeline.runner import PipelineRunner


class PipelineSource(Source):
    """
    Linear keyword source that assembles step definitions into a pipeline.
    """

    def __init__(self, steps: List[Dict[Literal["func_name", "args"], Union[str, dict]]], params: dict):
        super(PipelineSource, self).__init__()
        self.steps = [StepSource(**step) for step in steps]
        self.args = params

    def run(self, token, lib, env, logger=None):
        context = dict(token=token, library=lib, env=env, logger=logger)
        with PipelineRunner(flow=self, logger=logger, context=context) as runner:
            runner.run()
            return runner.context.instance.store.variables
