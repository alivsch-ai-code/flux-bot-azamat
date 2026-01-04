from typing import Dict
from src.domain.interfaces import UserRepository
from src.domain.entities import User

# Standard-Guthaben für neue User
DEFAULT_CREDITS = 2000

class InMemoryUserRepo(UserRepository):
    """
    Eine Datenbank, die nur im Arbeitsspeicher lebt.
    Ideal für Tests und einfache Deployments.
    """
    
    def __init__(self):
        # Unser "Speicher": Ein Dictionary {user_id: UserObjekt}
        self._storage: Dict[int, User] = {}

    def get_user(self, user_id: int) -> User:
        """
        Holt einen User. Wenn er nicht existiert, wird er 'on the fly' erstellt.
        """
        if user_id not in self._storage:
            # Neuen User anlegen (Lazy Creation)
            new_user = User(id=user_id, credits=DEFAULT_CREDITS)
            self._storage[user_id] = new_user
            return new_user
        
        return self._storage[user_id]

    def update_credits(self, user_id: int, amount: int):
        """
        Ändert das Guthaben.
        Amount kann negativ (Kosten) oder positiv (Aufladung) sein.
        """
        user = self.get_user(user_id)
        
        # Berechnung durchführen
        new_balance = user.credits + amount
        
        # Update speichern (im Dictionary ist das Referenz-basiert, 
        # aber wir machen es explizit für spätere SQL-Logik)
        user.credits = new_balance
        self._storage[user_id] = user
        
        # Optional: Loggen
        print(f"[DB] User {user_id}: Balance changed by {amount}. New: {new_balance}")