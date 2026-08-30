from abc import ABC, abstractmethod


class ImageProvider(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str
    ):
        pass