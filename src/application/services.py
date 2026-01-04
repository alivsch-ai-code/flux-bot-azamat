from src.domain.interfaces import UserRepository, AIProvider
from src.domain.entities import AIModel

class GenerationService:
    def __init__(self, repo: UserRepository, ai: AIProvider):
        self.repo = repo
        self.ai = ai

    def process_request(self, user_id: int, model: AIModel, prompt: str, image_url: str = None):
        # 1. User laden
        user = self.repo.get_user(user_id)
        
        # 2. Business Rule: Guthaben prüfen
        if user.credits < model.cost:
            return False, "Zu wenig Guthaben!"

        # 3. Security: Prompt Validierung (Hier könnte man noch einen Validator injecten)
        if len(prompt) > 1000 or "<script>" in prompt:
            return False, "Ungültiger Input."

        # 4. Generierung
        result = self.ai.generate(model, prompt, image_url)
        
        # 5. Abrechnung nur bei Erfolg
        if result.success:
            self.repo.update_credits(user_id, -model.cost)
            return True, result.data
        else:
            return False, f"Fehler: {result.error}"
# --- GET BALANCE --- 
    def get_balance(self, user_id: int) -> int:
        """
        Fragt das Repo nach dem aktuellen Kontostand des Users.
        """
        user = self.repo.get_user(user_id)
        return user.credits