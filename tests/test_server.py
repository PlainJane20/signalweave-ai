from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from northstar.contracts import DecisionReport
from northstar.server import NorthstarHandler


@pytest.fixture
def server_url():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), NorthstarHandler)
    except PermissionError:
        pytest.skip("environment does not permit binding a local test socket")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_dashboard_and_assets_are_served(server_url) -> None:
    with urlopen(f"{server_url}/", timeout=2) as response:
        html = response.read().decode("utf-8")
    with urlopen(f"{server_url}/static/styles.css", timeout=2) as response:
        css = response.read().decode("utf-8")
    with urlopen(f"{server_url}/static/app.js", timeout=2) as response:
        javascript = response.read().decode("utf-8")

    assert "SignalWeave AI" in html
    assert "--" in css
    assert "loadReport" in javascript


def test_health_endpoint_reports_offline_default(server_url, monkeypatch) -> None:
    monkeypatch.delenv("NORTHSTAR_PROVIDER", raising=False)

    with urlopen(f"{server_url}/api/health", timeout=2) as response:
        payload = json.loads(response.read())

    assert payload == {"status": "ok", "provider": "offline"}


def test_demo_report_endpoint_runs_checked_in_scenario(server_url, monkeypatch) -> None:
    monkeypatch.setenv("NORTHSTAR_PROVIDER", "offline")

    with urlopen(f"{server_url}/api/report", timeout=3) as response:
        report = DecisionReport.model_validate_json(response.read())

    assert report.scenario_id == "SCN-AURORA-2027"
    assert len(report.assessments) == 6


def test_analyze_endpoint_returns_typed_report(
    server_url, baseline_scenario, monkeypatch
) -> None:
    monkeypatch.setenv("NORTHSTAR_PROVIDER", "offline")
    body = baseline_scenario.model_dump_json().encode("utf-8")
    request = Request(
        f"{server_url}/api/analyze",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=3) as response:
        report = DecisionReport.model_validate_json(response.read())

    assert report.scenario_id == baseline_scenario.id
    assert len(report.assessments) == 6


def test_analyze_endpoint_rejects_invalid_input(server_url) -> None:
    request = Request(
        f"{server_url}/api/analyze",
        data=b'{"unexpected":true}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with pytest.raises(HTTPError) as caught:
        urlopen(request, timeout=2)

    assert caught.value.code == 400
    error = json.loads(caught.value.read())
    assert error["error"] == "invalid scenario"
