"""Tests für tests.support.in_memory_user_repo."""
from tests.support.in_memory_user_repo import InMemoryUserRepo


class TestInMemoryUserRepo:
    def test_get_user_creates_guest_if_not_exists(self):
        repo = InMemoryUserRepo()
        user = repo.get_user(99999)
        assert user.id == 99999
        assert user.username == "Guest"
        assert user.credits == 50

    def test_add_user_if_not_exists(self):
        repo = InMemoryUserRepo()
        repo.add_user_if_not_exists(1, "Alice")
        user = repo.get_user(1)
        assert user.username == "Alice"
        assert user.credits == 50

    def test_add_user_idempotent(self):
        repo = InMemoryUserRepo()
        repo.add_user_if_not_exists(1, "Alice")
        repo.add_user_if_not_exists(1, "Bob")  # sollte Alice behalten
        user = repo.get_user(1)
        assert user.username == "Alice"

    def test_update_credits_existing_user(self):
        repo = InMemoryUserRepo()
        repo.add_user_if_not_exists(1, "Alice")
        repo.update_credits(1, 10, "test")
        assert repo.get_user_credits(1) == 60

    def test_update_credits_new_user_creates_with_default_plus_amount(self):
        repo = InMemoryUserRepo()
        repo.update_credits(999, -5, "test")
        assert repo.get_user_credits(999) == 45  # 50 + (-5)
