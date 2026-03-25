"""Tests für Flask-Endpoints (main.app)."""
import io

import pytest
from unittest.mock import MagicMock


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


class TestApiModelOptionsSchema:
    """GET /api/model – generation_options_schema wird aus input_schema abgeleitet."""

    def test_api_model_includes_generation_options_schema(self, client, monkeypatch):
        import main as main_module
        from src.domain.entities import AIModel

        model = AIModel(
            key="google-veo-3-1",
            replicate_id="google/veo-3.1",
            name="Veo 3.1",
            description="Video model",
            internal_cost=200,
            custom_price=None,
        )
        model.input_schema = {
            "properties": {
                "duration": {"type": "integer", "default": 5, "enum": [5, 6, 7, 8]},
                "resolution": {"type": "string", "default": "1080p", "enum": ["720p", "1080p"]},
                "aspect_ratio": {"type": "string", "default": "16:9", "enum": ["16:9", "9:16"]},
                "reference_images": {"type": "array"},
                "generate_audio": {"type": "boolean", "default": True},
            }
        }

        fake_db = MagicMock()
        fake_db.get_model_by_key.return_value = model
        monkeypatch.setattr(main_module.app_runtime, "db", fake_db)

        r = client.get("/api/model?key=google-veo-3-1")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        gos = data["generation_options_schema"]
        assert gos["duration"]["enabled"] is True
        assert gos["duration"]["default"] == 5
        assert gos["resolution"]["enabled"] is True
        assert gos["aspect_ratio"]["enabled"] is True
        assert gos["reference_images"]["enabled"] is True
        assert gos["generate_audio"]["enabled"] is True
        assert "input_schema" in data
        assert "properties" in data["input_schema"]


class TestWebappUploadReference:
    """POST /api/webapp_upload_reference – Multipart, init_data, Replicate-Upload."""

    def test_no_db_returns_400(self, client):
        import main as main_module

        prev = main_module.app_runtime.db
        main_module.app_runtime.db = None
        try:
            r = client.post(
                "/api/webapp_upload_reference",
                data={"init_data": "x"},
                content_type="multipart/form-data",
            )
            assert r.status_code == 400
            assert r.get_json()["error"] == "no_db"
        finally:
            main_module.app_runtime.db = prev

    def test_missing_init_data(self, client, monkeypatch):
        import main as main_module

        monkeypatch.setattr(main_module.app_runtime, "db", MagicMock())
        r = client.post("/api/webapp_upload_reference", data={}, content_type="multipart/form-data")
        assert r.status_code == 400
        body = r.get_json()
        assert body["ok"] is False
        assert body["error"] == "missing_init_data"

    def test_no_files(self, client, monkeypatch):
        import main as main_module

        monkeypatch.setattr(main_module.app_runtime, "db", MagicMock())
        monkeypatch.setattr(
            "src.presentation.telegram.handlers.menu_handler._is_webapp_mode",
            lambda _db: True,
        )
        monkeypatch.setattr(
            "src.utils.telegram_init_data.validate_init_data",
            lambda _d, _t: 1,
        )
        r = client.post(
            "/api/webapp_upload_reference",
            data={"init_data": "ok"},
            content_type="multipart/form-data",
        )
        assert r.get_json()["error"] == "no_files"

    def test_success_returns_urls(self, client, monkeypatch):
        import main as main_module

        monkeypatch.setattr(main_module.app_runtime, "db", MagicMock())
        monkeypatch.setattr(
            "src.presentation.telegram.handlers.menu_handler._is_webapp_mode",
            lambda _db: True,
        )
        monkeypatch.setattr(
            "src.utils.telegram_init_data.validate_init_data",
            lambda _d, _t: 1,
        )

        fake_resp = MagicMock()
        fake_resp.url = "https://replicate.delivery/presigned/test.jpg"
        fake_client = MagicMock()
        fake_client.files.create.return_value = fake_resp

        monkeypatch.setattr("replicate.Client", lambda **kwargs: fake_client)

        r = client.post(
            "/api/webapp_upload_reference",
            data={
                "init_data": "ok",
                "files": (io.BytesIO(b"\xff\xd8\xff\xe0"), "shot.jpg"),
            },
            content_type="multipart/form-data",
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["urls"] == ["https://replicate.delivery/presigned/test.jpg"]
        fake_client.files.create.assert_called_once()
