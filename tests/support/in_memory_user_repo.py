"""In-Memory-Implementierung von `UserRepository` nur für Unit-Tests."""

from src.config.settings import config
from src.domain.entities import User
from src.domain.interfaces import UserRepository


class InMemoryUserRepo(UserRepository):
    def __init__(self):
        self.users = {}

    def get_user(self, user_id: int) -> User:
        if user_id not in self.users:
            return User(id=user_id, username="Guest", credits=int(config.START_CREDITS))

        u_data = self.users[user_id]
        return User(
            id=u_data["id"],
            username=u_data.get("username", "Unknown"),
            credits=u_data["credits"],
        )

    def add_user_if_not_exists(self, user_id: int, username: str):
        if user_id not in self.users:
            self.users[user_id] = {
                "id": user_id,
                "username": username,
                "credits": int(config.START_CREDITS),
            }

    def update_credits(self, user_id: int, amount: int, reason: str = ""):
        if user_id in self.users:
            self.users[user_id]["credits"] += amount
        else:
            self.users[user_id] = {
                "id": user_id,
                "username": "Unknown",
                "credits": int(config.START_CREDITS) + amount,
            }

    def get_user_credits(self, user_id: int) -> int:
        return self.get_user(user_id).credits
