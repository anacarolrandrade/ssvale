from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMClient(ABC):
    @abstractmethod
    def complete(self, messages: list[LLMMessage]) -> str:
        """Return model text for the given messages."""
