from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def load(self) -> list[dict]:
        pass