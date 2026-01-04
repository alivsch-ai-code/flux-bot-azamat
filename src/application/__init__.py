# src/application/services.py

from src.domain.interfaces import UserRepository, AIProvider
from src.domain.entities import AIModel, GenerationResult
from src.infrastructure.security.validator import InputValidator

class GenerationService:
    """
    Orchestriert den Prozess der Bild-/Textgenerierung.
    Verbindet Datenbank, Sicherheit und AI-Provider.
    """

    def __init__(self, repo: UserRepository, ai_provider: AIProvider):
        # Dependency Injection: Wir wissen nicht, welche DB oder welche AI genutzt wird.
        # Wir wissen nur, dass sie die Interfaces erfüllen.
        self.repo = repo
        self.ai = ai_provider

    def get_balance(self, user_id: int) -> int:
        """Liest nur das aktuelle Guthaben."""
        user = self.repo.get_user(user_id)
        return user.credits

    def process_request(self, user_id: int, model: AIModel, prompt: str, image_url: str = None):
        """
        Der Hauptprozess:
        1. Sicherheit prüfen
        2. Guthaben prüfen
        3. AI generieren lassen
        4. Abrechnen (nur bei Erfolg)
        """
        
        # 1. SECURITY: Input Validierung
        # Wir schützen uns vor Prompt Injection und bösen Befehlen
        if not InputValidator.validate_safety(prompt):
            return False, "⚠️ Deine Eingabe wurde aus Sicherheitsgründen abgelehnt."
        
        # Bereinigen (Whitespace, Länge kürzen)
        clean_prompt = InputValidator.sanitize_prompt(prompt)

        # 2. BUSINESS LOGIC: Guthaben prüfen
        user = self.repo.get_user(user_id)
        
        if user.credits < model.cost:
            missing = model.cost - user.credits
            return False, f"Zu wenig Guthaben! Dir fehlen {missing} Credits."

        # 3. INFRASTRUCTURE: AI Aufruf
        # Wir reichen den bereinigten Prompt weiter
        result: GenerationResult = self.ai.generate(model, clean_prompt, image_url)

        # 4. ACCOUNTING: Abrechnung
        if result.success:
            # Transaktion durchführen (Credits abziehen)
            self.repo.update_credits(user_id, -model.cost)
            return True, result.data
        else:
            # Keine Kosten bei Fehler
            return False, f"Fehler bei der Generierung: {result.error}"