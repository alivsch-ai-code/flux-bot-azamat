from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class User:
    id: int 
    username: str
    credits: int = 50

@dataclass
class AIModel:
    key: str
    replicate_id: str
    name: str
    cost: int
    type: List[str] 
    
    # NEU: Provider Feld (Wichtig für Unterscheidung Replicate vs. Andere)
    provider: str = "replicate" 
    
    description: str = ""
    original_dollar_per_run: Optional[float] = 0.0
    example_prompt: Optional[str] = None
    example_input_image: Optional[str] = None
    example_output_image: Optional[str] = None

@dataclass
class GenerationResult:
    success: bool
    data: Any = None 
    error: Optional[str] = None