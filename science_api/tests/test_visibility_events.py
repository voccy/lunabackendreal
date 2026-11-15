import main

def test_visibility_events_are_bounded_by_samples():
    samples=[{"datetime_utc":"2026-01-01T00:00:00Z","sun_visible":False},
             {"datetime_utc":"2026-01-01T00:10:00Z","sun_visible":True},
             {"datetime_utc":"2026-01-01T00:20:00Z","sun_visible":True},
             {"datetime_utc":"2026-01-01T00:30:00Z","sun_visible":False}]
    events=main.visibility_events(samples,"sun_visible","sunrise","sunset")
    assert [x["type"] for x in events]==["sunrise","sunset"]
    assert events[0]["bounded_by_utc"]==["2026-01-01T00:00:00Z","2026-01-01T00:10:00Z"]
    assert events[1]["datetime_utc"]=="2026-01-01T00:30:00Z"
    assert main.visibility_events(samples,"sun_visible","sunrise","sunset")[0]["accuracy"].startswith("sample-resolution")

def test_no_crossing_for_constant_visibility():
    samples=[{"datetime_utc":"2026-01-01T00:00:00Z","v":True},
             {"datetime_utc":"2026-01-01T00:10:00Z","v":True}]
    assert main.visibility_events(samples,"v","rise","set")==[]
