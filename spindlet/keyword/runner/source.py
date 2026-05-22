from spindlet.keyword.runner.flow import Flow


class Source(Flow):
    """ 关键字资源定义器基类 """
    pass


class StepSource(Source):
    """ 测试步骤定义器 """

    def __init__(self, func_name, args):
        super(StepSource, self).__init__()
        self.func_name = func_name
        self.args = args
