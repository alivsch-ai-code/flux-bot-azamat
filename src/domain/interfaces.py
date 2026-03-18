from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities import User, AIModel, GenerationResult, MediaFile

# Vertrag für Datenbanken
class UserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: int) -> User: pass

    @abstractmethod
    def update_credits(self, user_id: int, amount: int): pass


# Vertrag für AI Provider
class AIProvider(ABC):
    @abstractmethod
    def generate(
        self,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
    ) -> GenerationResult: pass