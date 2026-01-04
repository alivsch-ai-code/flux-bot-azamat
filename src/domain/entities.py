from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    credits: int

@dataclass
class AIModel:
    key: str
    replicate_id: str  # Kann leer sein bei Sonauto
    name: str
    cost: int
    type: str
    provider: str = "replicate"  # <--- NEU! Standard ist Replicate

@dataclass
class GenerationResult:
    success: bool
    data: Optional[str] = None
    error: Optional[str] = None