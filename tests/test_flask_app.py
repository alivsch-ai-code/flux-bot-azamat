"""Tests für Flask-Endpoints (main.app)."""
import pytest


@pytest.fixture
def client():
    """Flask Test-Client. main muss nach setzen der Env-Vars importiert werden."""
    from main import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthCheck:
    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "ONLINE" in r.data.decode()

    def test_root_returns_text(self, client):
        r = client.get("/")
        assert "System Status" in r.data.decode() or "ONLINE" in r.data.decode()


class TestApiStrings:
    def test_strings_default_lang(self, client):
        r = client.get("/api/strings")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, dict)
        assert "webapp_title" in data

    def test_strings_lang_param(self, client):
        r = client.get("/api/strings?lang=en")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, dict)

    def test_strings_invalid_lang_fallback_de(self, client):
        r = client.get("/api/strings?lang=xy")
        assert r.status_code == 200


class TestApiShopPackages:
    """GET /api/shop_packages – Credit-Pakete für WebApp."""

    def test_shop_packages_returns_200_and_list(self, client):
        r = client.get("/api/shop_packages")
        assert r.status_code == 200
        data = r.get_json()
        assert data is not None
        assert "packages" in data
        assert isinstance(data["packages"], list)

    def test_shop_packages_structure(self, client):
        r = client.get("/api/shop_packages")
        data = r.get_json()
        for pkg in data.get("packages", []):
            assert "label" in pkg
            assert "credits" in pkg
            assert "price" in pkg
