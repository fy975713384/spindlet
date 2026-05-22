from enum import Enum


class FlowStateEnum(Enum):
    FLOW_WAITING = "waiting"
    FLOW_RUNNING = "running"
    FLOW_SUCCESS = "success"
    FLOW_FAILURE = "failure"
    FLOW_BLOCKING = "blocking"
    FLOW_CANCEL = "cancel"
    FLOW_ERROR = "error"


class Flow:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.__state = FlowStateEnum.FLOW_WAITING

    @property
    def name(self):
        raise NotImplemented

    @property
    def state(self) -> FlowStateEnum:
        return self.__state

    @state.setter
    def state(self, value: FlowStateEnum):
        self.__state = value
