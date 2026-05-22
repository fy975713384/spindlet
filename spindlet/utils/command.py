from abc import ABCMeta, abstractmethod


class Cmd(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
