"""The dashboard theme catalogue served to the SPA's picker and first paint."""

import pytest

import hermes_cli.config as _cfg_mod


class TestDashboardThemeCatalogue:
    @pytest.fixture(autouse=True)
    def _home(self, _isolate_hermes_home):
        pass

    @staticmethod
    def _client():
        from starlette.testclient import TestClient

        from hermes_cli import web_server

        client = TestClient(web_server.app)
        client.headers[web_server._SESSION_HEADER_NAME] = web_server._SESSION_TOKEN
        return client

    def test_clarity_themes_lead_the_picker_and_persist(self):
        client = self._client()
        names = [t["name"] for t in client.get("/api/dashboard/themes").json()["themes"]]
        assert names[:2] == ["clarity", "clarity-dark"]

        assert client.put("/api/dashboard/theme", json={"name": "clarity-dark"}).status_code == 200
        assert client.get("/api/dashboard/themes").json()["active"] == "clarity-dark"

    def test_a_config_without_a_theme_reports_clarity(self, monkeypatch):
        monkeypatch.setattr(_cfg_mod, "load_config", lambda: {"dashboard": {}})
        assert self._client().get("/api/dashboard/themes").json()["active"] == "clarity"

    def test_the_config_page_offers_the_clarity_themes(self):
        fields = self._client().get("/api/config/schema").json()["fields"]
        assert {"clarity", "clarity-dark"} <= set(fields["dashboard.theme"]["options"])
