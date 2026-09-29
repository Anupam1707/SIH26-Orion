def test_districts_returns_geojson_from_the_scenario(client, scenario):
    body = client.get("/districts").json()
    assert body["type"] == "FeatureCollection"
    assert [f["id"] for f in body["features"]] == [d.id for d in scenario.districts]
    for feat, d in zip(body["features"], scenario.districts):
        assert feat["geometry"] == {"type": "Polygon", "coordinates": d.polygon}
        assert feat["properties"]["name"] == d.name
        assert feat["properties"]["neighbours"] == d.neighbours


def test_health_reports_demo_clock_at_end_of_history(client, scenario):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["seed"] == 42
    assert len(body["scenario_hash"]) == 16
    assert body["demo_clock"] == scenario.history_end.isoformat()
