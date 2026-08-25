from abc import ABC, abstractmethod

from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodeBase(ABC):
    name='node_base'
    def __init__(self):
        if self.name == 'node_base':
            logger.error('节点名字没定义')
            raise ValueError('节点名字没定义')
    def __call__(self, state:ImportGraphState):
        try:
            logger.info(f'节点{self.name}开始')
            res= self.process(state)
            logger.info(f'节点{self.name}结束')
            return res
        except Exception as e:
            logger.error(e)
    @abstractmethod
    def process(self,state:ImportGraphState):
        pass
