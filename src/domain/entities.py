from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Dict


class MediaType(str, Enum):
    """Unterstützte Medientypen für Modell-Inputs."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


@dataclass
class MediaFile:
    """Repräsentiert eine hochgeladene Datei (Bild, Video, Audio, Dokument)."""
    path: str
    media_type: MediaType
    mime_type: Optional[str] = None

    @property
    def extension(self) -> str:
        import os
        return os.path.splitext(self.path)[1].lower()


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
    description: str
    
    # --- NEUE PREIS STRUKTUR ---
    base_cost_usd: float = 0.0      
    internal_cost: int = 10        
    custom_price: Optional[int] = None 
    
    # --- METADATA ---
    provider: str = "replicate" 
    type: List[str] = field(default_factory=list)
    menu_path: str = "root"
    is_active: bool = True 
    is_favorite: bool = False
    is_commercial: bool = True
    manual_override: bool = False
    
    # --- DYNAMISCHE DATEN ---
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    example_data: Dict[str, Any] = field(default_factory=dict)
    
    # ALTE FELDER (OPTIONAL/COMPATIBILITY)
    example_prompt: Optional[str] = None
    example_input_image: Optional[str] = None
    example_output_image: Optional[str] = None

    @property
    def final_cost(self) -> int:
        """Gibt den endgültigen Preis zurück (Custom > Internal)."""
        if self.custom_price is not None:
            return self.custom_price
        return self.internal_cost

    @property
    def cost(self) -> int:
        """
        RÜCKWÄRTSKOMPATIBILITÄT:
        Damit alter Code (wie keyboards.py), der 'model.cost' aufruft, 
        nicht abstürzt, leiten wir das hier an final_cost weiter.
        """
        return self.final_cost

@dataclass
class GenerationResult:
    success: bool
    data: Any = None  # URL(s), Text, oder Liste von URLs
    error: Optional[str] = None