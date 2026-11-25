import csv, io, json, os, sys
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as app_module
from cognifin.quiz import score_quiz, ITEMS
from cognifin.simulator import generate_prices, Portfolio, detect, N_TURNS
from cognifin.mismatch import detect_mismatches
from cognifin.session import Session
from cognifin.coach_llm import _valid, _offline_message, why_this
from cognifin.user_model import UserModel


def test_http_csv_export_returns_a_downloadable_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "ROOT", str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), app_module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    session_id = None
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        request = Request(
            base + "/api/start",
            data=json.dumps({"user_id": "qa-export", "coach_mode": "none"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            session_id = json.load(response)["session_id"]

        step_request = Request(
            base + f"/api/session/{session_id}/step",
            data=json.dumps({"action": {"type": "hold"}, "decision_ms": 5000}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(step_request, timeout=5) as response:
            assert response.status == 200

        with urlopen(f"{base}/api/session/{session_id}/export", timeout=5) as response:
            content = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/csv"
            assert response.headers["Content-Disposition"].endswith(
                f"filename=session_{session_id}.csv")
            assert "session_id,user_id,coach_mode" in content.splitlines()[0]
            assert "market_observations" in content.splitlines()[0]
            rows = list(csv.DictReader(io.StringIO(content)))
            assert len(rows) == 1
            assert rows[0]["session_id"] == session_id
    finally:
        if session_id:
            app_module.SESSIONS.pop(session_id, None)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_prices_deterministic_and_length():
    a, b = generate_prices(5), generate_prices(5)
    assert a == b and all(len(v) == N_TURNS + 1 for v in a.values())
    assert generate_prices(5) != generate_prices(6)


def test_quiz_scoring_and_reverse_items():
    hi = {i: 5 for i, *_ in ITEMS}
    lo = {i: 1 for i, *_ in ITEMS}
    assert score_quiz(hi)["traits"]["loss_aversion"] == 1.0
    assert score_quiz(lo)["traits"]["loss_aversion"] == 0.0
    # herding has one reverse-coded item (hf3): all-5 gives (1+1+0)/3
    assert abs(score_quiz(hi)["traits"]["herding_fomo"] - 2 / 3) < 0.01
    assert score_quiz({})["traits"]["panic_selling"] == 0.5


def test_panic_sell_detected_on_realised_loss():
    prices = {"BOND": [100] * 4, "INDEX": [100, 100, 100, 100], "TECH": [100, 110, 118, 100]}
    pf = Portfolio(0)
    pf.units["TECH"], pf.cost["TECH"] = 10, 115.0
    ev, ctx = detect(prices, 3, pf, {"type": "sell", "asset": "TECH", "fraction": 1.0}, [])
    assert any(e["type"] == "panic_sell" for e in ev) and "dip" in ctx


def test_no_panic_when_selling_at_gain():
    prices = {"BOND": [100] * 4, "INDEX": [100] * 4, "TECH": [100, 120, 130, 120]}
    pf = Portfolio(0)
    pf.units["TECH"], pf.cost["TECH"] = 10, 100.0
    ev, _ = detect(prices, 3, pf, {"type": "sell", "asset": "TECH", "fraction": 1.0}, [])
    assert not any(e["type"] == "panic_sell" for e in ev)


def test_fomo_and_concentration():
    prices = {"BOND": [100] * 4, "INDEX": [100] * 4, "TECH": [100, 105, 110, 115]}
    pf = Portfolio(10000)
    ev, ctx = detect(prices, 3, pf, {"type": "buy", "asset": "TECH", "fraction": 0.9}, [])
    kinds = {e["type"] for e in ev}
    assert {"fomo_buy", "overconcentration"} <= kinds and "rally" in ctx


def test_zero_cash_buy_is_not_detected_as_trade():
    prices = {"BOND": [100] * 4, "INDEX": [100] * 4, "TECH": [100, 105, 110, 115]}
    pf = Portfolio(0)
    history = [{"type": "buy"}] * 4
    events, _ = detect(prices, 3, pf, {"type": "buy", "asset": "TECH", "fraction": 0.8},
                       history, buy_amount=0)
    assert not events


def test_mismatch_requires_claim():
    ev = [{"type": "panic_sell", "asset": "TECH", "drop_pct": -6.0, "loss_vs_cost_pct": -3.0}]
    assert detect_mismatches({"self_risk_tolerance": 0.9}, {}, ev)
    assert not detect_mismatches({"self_risk_tolerance": 0.2, "self_calm_under_loss": 0.2}, {}, ev)


def test_baseline_ignores_profile_llm_uses_it():
    ans_hi = {i: 5 for i, *_ in ITEMS}
    ans_lo = {i: 1 for i, *_ in ITEMS}
    out = {}
    for name, ans in (("hi", ans_hi), ("lo", ans_lo)):
        s = Session(name, ans, "llm", seed=1, use_api=False, persist=False)
        out[name] = _offline_message(s.um, {"type": "overtrading", "trades_in_last_5": 5}, [])
    assert out["hi"] != out["lo"]


@pytest.mark.parametrize(("event", "expected_evidence"), [
    ({"type": "panic_sell", "asset": "TECH", "drop_pct": -6.2,
      "loss_vs_cost_pct": -4.1}, "Sold TECH after a 6.2% drop"),
    ({"type": "fomo_buy", "asset": "INDEX", "recent_gain_pct": 12.4},
     "rose 12.4% over three turns"),
    ({"type": "overconcentration", "asset": "TECH", "weight_pct": 76},
     "represented 76% of portfolio value"),
    ({"type": "overtrading", "trades_in_last_5": 5},
     "Traded on 5 consecutive turns"),
    ({"type": "hold_loser", "asset": "INDEX", "loss_vs_cost_pct": -11.2,
      "turns": 3}, "11.2% below average cost for 3 turns"),
    ({"type": "early_profit_take", "asset": "INDEX", "gain_pct": 3.1,
      "loser": "TECH"}, "Sold INDEX at a 3.1% gain"),
])
def test_why_this_explains_event_evidence_and_limits(event, expected_evidence):
    explanation = why_this(UserModel("why-this", {}, {}), event, [])

    assert expected_evidence in explanation["event_evidence"]
    assert explanation["event_mechanism"]
    assert explanation["trait_definition"]
    assert explanation["reflection_question"]
    assert "not diagnoses" in explanation["profile_note"]
    assert "cannot know your intention" in explanation["limitations"]
    assert explanation["citation"]


def test_session_runs_and_exports_csv(tmp_path):
    s = Session("u", {}, "llm", seed=3, use_api=False, persist=True, profile_dir=str(tmp_path))
    for _ in range(N_TURNS):
        s.step({"type": "hold"}, 5000)
    assert s.state()["done"] and s.to_csv().count("\n") == N_TURNS + 1
    assert (tmp_path / "u.json").exists()
    rows = list(csv.DictReader(io.StringIO(s.to_csv())))
    assert all(row["event_types"] == "none" for row in rows)
    assert all(row["mismatch_codes"] == "none" for row in rows)
    assert all(row["coach_source"] == "not_triggered" for row in rows)
    assert all("No behavioural pattern" in row["coach_message"] for row in rows)


def test_multi_asset_decisions_use_starting_cash_and_sell_per_holding():
    s = Session("multi", {}, "none", seed=3, use_api=False, persist=False)
    actions = [
        {"type": "buy", "asset": "BOND", "fraction": 0.2},
        {"type": "buy", "asset": "INDEX", "fraction": 0.3},
        {"type": "hold", "asset": "TECH", "fraction": 0},
    ]
    s.step(actions, 3000)
    assert s.turn == 1
    assert s.pf.cash == pytest.approx(5000)
    assert s.pf.units["BOND"] == pytest.approx(20)
    assert s.pf.units["INDEX"] == pytest.approx(30)

    units = s.pf.units["BOND"]
    s.step([
        {"type": "sell", "asset": "BOND", "fraction": 0.5},
        {"type": "hold", "asset": "INDEX", "fraction": 0},
        {"type": "hold", "asset": "TECH", "fraction": 0},
    ], 2000)
    assert s.pf.units["BOND"] == pytest.approx(units / 2)
    row = list(csv.DictReader(io.StringIO(s.to_csv())))[0]
    assert row["action_type"] == "multi"
    assert json.loads(row["actions"]) == actions


def test_multi_asset_buy_allocation_cannot_exceed_starting_cash():
    s = Session("multi", {}, "none", seed=3, use_api=False, persist=False)
    with pytest.raises(ValueError, match="cannot exceed 100%"):
        s.step([
            {"type": "buy", "asset": "BOND", "fraction": 0.6},
            {"type": "buy", "asset": "INDEX", "fraction": 0.5},
            {"type": "hold", "asset": "TECH", "fraction": 0},
        ], 1000)
    assert s.turn == 0
    assert s.pf.cash == pytest.approx(10000)


def test_multi_asset_actions_count_as_one_trading_turn():
    s = Session("multi", {}, "none", seed=100, use_api=False, persist=False)
    actions = [
        {"type": "buy", "asset": asset, "fraction": 0.1}
        for asset in ("BOND", "INDEX", "TECH")
    ]
    for _ in range(4):
        result = s.step(actions, 1000)
        assert not any(e["type"] == "overtrading" for e in result["events"])
    result = s.step(actions, 1000)
    assert [e["type"] for e in result["events"]].count("overtrading") == 1


def test_multi_asset_rally_buy_triggers_coach_event():
    seed = next(s for s in range(1000)
                if generate_prices(s)["TECH"][3] / generate_prices(s)["TECH"][0] >= 1.10)
    s = Session("multi", {}, "llm", seed=seed, use_api=False, persist=False)
    for _ in range(3):
        s.step({"type": "hold"}, 1000)
    result = s.step([
        {"type": "hold", "asset": "BOND", "fraction": 0},
        {"type": "hold", "asset": "INDEX", "fraction": 0},
        {"type": "buy", "asset": "TECH", "fraction": 0.4},
    ], 1000)
    assert any(e["type"] == "fomo_buy" for e in result["events"])
    assert result["coaching"]


def test_market_context_observation_surfaces_weaker_trend_without_bias_label():
    seed = next(s for s in range(1000)
                if 0.05 <= generate_prices(s)["INDEX"][3] /
                generate_prices(s)["INDEX"][0] - 1 < 0.10
                and all(generate_prices(s)[asset][3] /
                        generate_prices(s)[asset][0] - 1 < 0.10
                        for asset in ("INDEX", "TECH")))
    s = Session("observe", {}, "llm", seed=seed, use_api=False, persist=False)
    initial_traits = dict(s.um.long_term)
    for _ in range(3):
        s.step({"type": "hold"}, 1000)
    result = s.step([
        {"type": "hold", "asset": "BOND", "fraction": 0},
        {"type": "buy", "asset": "INDEX", "fraction": 0.1},
        {"type": "hold", "asset": "TECH", "fraction": 0},
    ], 1000)

    assert not result["events"]
    assert result["observations"][0]["type"] == "buy_after_rise"
    assert s.um.long_term == initial_traits
    assert s.summary()["observation_counts"]["buy_after_rise"] == 1


def test_sell_context_observations_are_logged_without_bias_events():
    s = Session("observe", {}, "none", seed=1, use_api=False, persist=False)
    s.turn = 3
    s.pf.units["INDEX"] = 10
    s.pf.cost["INDEX"] = s.px()["INDEX"] * 0.9

    result = s.step({"type": "sell", "asset": "INDEX", "fraction": 0.1}, 1000)

    kinds = {observation["type"] for observation in result["observations"]}
    assert "sell_after_drop" in kinds
    assert not result["events"]
    row = next(csv.DictReader(io.StringIO(s.to_csv())))
    assert {observation["type"] for observation in json.loads(row["market_observations"])} == kinds


def test_sell_below_cost_and_hold_during_drop_are_observed():
    sell = Session("observe-sell", {}, "none", seed=3, use_api=False, persist=False)
    sell.turn = 3
    sell.pf.units["INDEX"] = 10
    sell.pf.cost["INDEX"] = sell.px()["INDEX"] * 1.1
    sell_result = sell.step({"type": "sell", "asset": "INDEX", "fraction": 0.1}, 1000)
    assert any(o["type"] == "sell_below_cost" for o in sell_result["observations"])

    hold = Session("observe-hold", {}, "none", seed=0, use_api=False, persist=False)
    hold.turn = 8
    hold.pf.units["TECH"] = 1
    hold.pf.cost["TECH"] = hold.prices["TECH"][7]
    hold_result = hold.step({"type": "hold", "asset": "TECH"}, 1000)
    assert any(o["type"] == "hold_during_drop" for o in hold_result["observations"])


def test_reflection_summary_tracks_plan_actions_and_confidence():
    s = Session("reflect", {}, "none", seed=3, use_api=False, persist=False,
                plan="  Pause   before price swings. ")
    s.step([
        {"type": "buy", "asset": "BOND", "fraction": 0.1},
        {"type": "hold", "asset": "INDEX", "fraction": 0},
        {"type": "hold", "asset": "TECH", "fraction": 0},
    ], 2000, "following_plan", 4)
    s.step([
        {"type": "hold", "asset": "BOND", "fraction": 0},
        {"type": "hold", "asset": "INDEX", "fraction": 0},
        {"type": "hold", "asset": "TECH", "fraction": 0},
    ], 2000, "not_recorded", None)

    summary = s.summary()
    assert summary["plan"] == "Pause before price swings."
    assert summary["actions_by_asset"]["BOND"] == {"buy": 1, "sell": 0, "hold": 1}
    assert summary["reflection_turns"] == 1
    assert summary["average_confidence"] == 4


def test_llm_output_validator():
    assert _valid("You sold quickly after a drop. Pause a turn next time.")
    assert not _valid("This will recover, guaranteed!")
    assert not _valid("")


def test_long_term_updates_and_decay():
    um = UserModel("x", {"panic_selling": 0.5}, {})
    um.update_long_term([{"type": "panic_sell"}], ["dip"])
    assert um.long_term["panic_selling"] > 0.5
    v = um.long_term["panic_selling"]
    um.update_long_term([], ["dip"])
    assert um.long_term["panic_selling"] < v


# ---- Bayesian user model -----------------------------------------------------------
def test_bayesian_prior_equals_quiz_and_uncertainty_shrinks_with_evidence():
    um = UserModel("x", {"panic_selling": 0.3}, {})
    assert um.long_term["panic_selling"] == pytest.approx(0.3)
    sd0 = um.uncertainty("panic_selling")
    for _ in range(10):
        um.update_long_term([{"type": "panic_sell"}], ["dip"])
    assert um.long_term["panic_selling"] > 0.3
    assert um.uncertainty("panic_selling") < sd0
    assert um.evidence["panic_selling"] == [10, 0]        # fired turns are not also "resisted"


def test_opportunity_counts_once_per_turn_and_overconfidence_is_confirm_only():
    um = UserModel("x", {}, {})
    um.update_long_term([{"type": "overtrading"}, {"type": "overconcentration"}], ["dip", "dip"])
    assert um.evidence["overconfidence"] == [1, 0]
    assert um.evidence["panic_selling"] == [0, 1]
    um.update_long_term([], ["rally", "loser"])
    assert um.evidence["herding_fomo"] == [0, 1] and um.evidence["loss_aversion"] == [0, 1]
    assert um.evidence["overconfidence"] == [1, 0]


def test_profile_persistence_carries_discounted_evidence(tmp_path):
    um = UserModel("P9", {"herding_fomo": 0.5}, {})
    for _ in range(4):
        um.update_long_term([{"type": "fomo_buy"}], ["rally"])
    um.save(str(tmp_path))
    again = UserModel.load_or_new("P9", {"herding_fomo": 0.2}, {}, str(tmp_path))
    assert again.quiz_traits["herding_fomo"] == 0.2          # fresh quiz kept for mismatch checks
    assert again.evidence["herding_fomo"] == [2.0, 0.0]      # 0.5 carry-over
    assert again.long_term["herding_fomo"] > 0.2


def test_legacy_profile_without_evidence_still_loads(tmp_path):
    (tmp_path / "old.json").write_text(json.dumps({"long_term": {"panic_selling": 0.9}}))
    um = UserModel.load_or_new("old", {"panic_selling": 0.1}, {}, str(tmp_path))
    assert um.quiz_traits["panic_selling"] == 0.1
    assert um.long_term["panic_selling"] == pytest.approx(0.5)


def test_loser_context_marks_loss_aversion_opportunity():
    prices = {"BOND": [100] * 4, "INDEX": [100] * 4, "TECH": [100, 95, 90, 85]}
    pf = Portfolio(0)
    pf.units["TECH"], pf.cost["TECH"] = 10, 100.0
    _, ctx = detect(prices, 3, pf, {"type": "hold"}, [])
    assert "loser" in ctx


def test_rally_is_not_an_opportunity_without_cash():
    prices = {"BOND": [100] * 4, "INDEX": [100] * 4, "TECH": [100, 105, 110, 115]}
    _, ctx = detect(prices, 3, Portfolio(0), {"type": "hold"}, [])
    assert "rally" not in ctx


def test_why_this_reports_uncertainty_and_evidence():
    um = UserModel("x", {"panic_selling": 0.6}, {})
    um.update_long_term([{"type": "panic_sell"}], ["dip"])
    w = why_this(um, {"type": "panic_sell", "asset": "TECH", "drop_pct": -8.0,
                      "loss_vs_cost_pct": -12.0}, [])
    assert w["evidence_count"] == 1 and 0 < w["trait_uncertainty"] < 0.2
    assert "±" in w["profile_note"]


# ---- LLM response handling ----------------------------------------------------------
def test_llm_text_extraction_rejects_truncated_and_skips_thoughts():
    from cognifin.coach_llm import _extract_text
    ok = {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"text": "internal reasoning", "thought": True}, {"text": "You sold after a drop."}]}}]}
    assert _extract_text(ok) == "You sold after a drop."
    cut = {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "You so"}]}}]}
    assert _extract_text(cut) is None
    assert _extract_text({"candidates": []}) is None


# ---- evaluation harness -------------------------------------------------------------
def test_eval_mismatch_flag_ignores_none_sentinel():
    from cognifin.evaluate import session_metrics
    s = Session("e", {}, coach_mode="none", seed=1, use_api=False, persist=False)
    s.step({"type": "hold"})
    assert s.log[0]["mismatch_codes"] == "none"
    m = session_metrics(s, [[]], [])
    assert m["mismatch_flagged"] is False and m["any_mismatch_flagged"] is False


def test_repeated_pattern_is_not_recoached_within_cooldown():
    from cognifin.session import COACH_COOLDOWN_TURNS
    s = Session("cd", {}, coach_mode="baseline", seed=1, use_api=False, persist=False)
    ev = {"type": "hold_loser", "asset": "INDEX", "loss_vs_cost_pct": -12.0, "turns": 3}
    import cognifin.session as sess
    orig = sess.detect
    sess.detect = lambda *a, **k: ([dict(ev)], [])
    try:
        sources = [s.step({"type": "hold"})["coaching"] for _ in range(COACH_COOLDOWN_TURNS + 2)]
    finally:
        sess.detect = orig
    assert len(sources[0]) == 1 and all(not c for c in sources[1:COACH_COOLDOWN_TURNS + 1])
    assert len(sources[COACH_COOLDOWN_TURNS + 1]) == 1
    assert s.log[1]["coach_source"] == "cooldown" and s.log[1]["event_types"] == "hold_loser"


def test_http_start_accepts_numeric_seed_and_ignores_bad_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "ROOT", str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), app_module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ids = []
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        for seed in (42, "42", "abc", -3):
            req = Request(base + "/api/start", headers={"Content-Type": "application/json"},
                          data=json.dumps({"user_id": "seed", "coach_mode": "none", "seed": seed}).encode())
            with urlopen(req, timeout=5) as response:
                ids.append(json.load(response)["session_id"])
        sessions = [app_module.SESSIONS[i] for i in ids]
        assert sessions[0].seed == sessions[1].seed == 42
        assert sessions[0].prices == generate_prices(42)
        assert isinstance(sessions[2].seed, int) and isinstance(sessions[3].seed, int)
    finally:
        for i in ids:
            app_module.SESSIONS.pop(i, None)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_llm_call_retries_once_on_transient_503(monkeypatch):
    import urllib.error
    from cognifin import coach_llm
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(coach_llm, "RETRY_WAIT_S", 0)
    calls = []

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self):
            return json.dumps({"candidates": [{"finishReason": "STOP",
                               "content": {"parts": [{"text": "ok"}]}}]}).encode()

    def fake(req, timeout=0):
        calls.append(1)
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, None)
        return Resp()
    monkeypatch.setattr(coach_llm.urllib.request, "urlopen", fake)
    assert coach_llm._call_llm("s", "u") == "ok" and len(calls) == 2


def test_llm_call_falls_back_to_second_model_when_primary_is_exhausted(monkeypatch):
    import urllib.error
    from cognifin import coach_llm
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.delenv("COGNIFIN_MODEL", raising=False)
    monkeypatch.setenv("COGNIFIN_FALLBACK_MODEL", "backup-model")
    monkeypatch.setattr(coach_llm, "RETRY_WAIT_S", 0)
    urls = []

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self):
            return json.dumps({"candidates": [{"finishReason": "STOP",
                               "content": {"parts": [{"text": "from backup"}]}}]}).encode()

    def fake(req, timeout=0):
        urls.append(req.full_url)
        if "backup-model" not in req.full_url:
            raise urllib.error.HTTPError(req.full_url, 429, "quota", {}, None)
        return Resp()
    monkeypatch.setattr(coach_llm.urllib.request, "urlopen", fake)
    assert coach_llm._call_llm("s", "u") == "from backup"
    assert len(urls) == 3 and coach_llm.LAST_MODEL == "backup-model"
