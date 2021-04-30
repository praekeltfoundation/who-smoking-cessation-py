from who.main import app


def test_metrics():
    _, response = app.test_client.get(app.url_for("metrics"))
    assert response.status == 200
    assert "sanic_request_latency_sec" in response.text


def test_health():
    _, response = app.test_client.get(app.url_for("health"))
    assert response.status == 200
    assert isinstance(response.json["amqp"].pop("time_since_last_heartbeat"), float)
    assert isinstance(response.json["redis"].pop("response_time"), float)
    assert response.json == {
        "status": "ok",
        "amqp": {"connection": True},
        "redis": {"connection": True},
    }


# TODO: Tests for when services are down. These tests are currently done manually
