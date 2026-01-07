from src.domain.interfaces import UserRepository
from src.domain.entities import User

class InMemoryUserRepo(UserRepository):
    def __init__(self):
        # Hier speichern wir die User-Daten
        # Format: {12345: {"id": 12345, "username": "Aljoscha", "credits": 50}}
        self.users = {}

    def get_user(self, user_id: int) -> User:
        # Fall 1: User existiert noch nicht im Speicher
        if user_id not in self.users:
            # Wir erstellen ein temporäres Objekt (Default: Guest)
            return User(id=user_id, username="Guest", credits=50)
        
        # Fall 2: User existiert -> Daten laden
        u_data = self.users[user_id]
        
        # FIX: Hier fehlte vorher das 'username'-Argument!
        # Wir nutzen .get("username", "Unknown"), falls alte Daten ohne Namen da sind
        return User(
            id=u_data["id"], 
            username=u_data.get("username", "Unknown"), 
            credits=u_data["credits"]
        )

    def add_user_if_not_exists(self, user_id: int, username: str):
        if user_id not in self.users:
            # Hier legen wir den User initial an
            self.users[user_id] = {
                "id": user_id, 
                "username": username, 
                "credits": 50
            }

    def update_credits(self, user_id: int, amount: int, reason: str = ""):
        if user_id in self.users:
            self.users[user_id]["credits"] += amount
        else:
            # Fallback: User existiert nicht, wir legen ihn mit Startguthaben + Betrag an
            self.users[user_id] = {
                "id": user_id, 
                "username": "Unknown", 
                "credits": 50 + amount
            }

    def get_user_credits(self, user_id: int) -> int:
        return self.get_user(user_id).credits