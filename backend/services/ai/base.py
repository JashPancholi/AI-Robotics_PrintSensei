from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def generate_structured_output(
        self,
        prompt: str,
        schema: dict
    ):
        pass