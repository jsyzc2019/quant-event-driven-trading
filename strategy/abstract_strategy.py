from abc import ABC, abstractmethod

import pandas as pd


class AbstractStrategy(ABC):
    SUFFIX = '_STRATEGY'
    NAME = ""

    @abstractmethod
    def entry(self, ohlcv: pd.DataFrame):
        raise NotImplementedError

    @abstractmethod
    def exit(self, ohlcv: pd.DataFrame):
        raise NotImplementedError

    def __str__(self) -> str:
        return f'{self.SUFFIX}{self.NAME}'
