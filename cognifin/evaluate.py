"""Offline evaluation with SIMULATED personas (not human participants).

Three kinds of result:
 A. Pipeline checks that do not depend on any assumed response to coaching:
    - mismatch-detection recall / false-positive rate vs persona ground truth
      (ground truth = "claims high risk tolerance AND truly panic-prone", so it is scored
      against the two panic-related mismatch codes only)
    - trait estimation: quiz-only vs Bayesian quiz+behaviour (top-trait accuracy and MAE),
      with an honest quiz and with a bias-blind-spot quiz (under-reported traits)
 B. Sensitivity analysis of "behavioural shift" under an ASSUMED heed model.
 C. Message-grounding checks on coach output (own numbers cited, correct trait, validity).

Run:  python -m cognifin.evaluate --n 300 --out results
"""
import argparse
import csv
import json
import os
import random
import statistics as stats

from .agents import Persona
from .knowledge import EVENT_TO_TRAIT, TRAIT_KEYS
from .session import Session
from .simulator import N_TURNS

HEED_BASE = 0.35          # assumed prob. a generic message changes behaviour
BLIND_SPOT = 0.35         # max per-trait under-reporting in the blind-spot quiz condition
PANIC_CODES = {"risk_claim_vs_panic", "calm_claim_vs_panic"}


def _codes(row):
    return {c for c in row["mismatch_codes"].split("|") if c and c != "none"}


def play(persona, answers, mode, seed, heed, user_id):
    s = Session(user_id, answers, coach_mode=mode, seed=seed, use_api=False, persist=False)
    persona.suppress = {}
    persona.rng = random.Random(seed + 1)      # same behavioural noise stream in every condition
    events_by_turn, coached = [], []
    while s.turn < N_TURNS:
        st = s.state()
        act, ms = persona.act(st, s.prices)
        r = s.step(act, ms)
        events_by_turn.append([e["type"] for e in r["events"]])
        if r["coaching"]:
            persona.hear(r["coaching"], heed)
            coached.append((s.turn, [c["trait"] for c in r["coaching"]]))
        persona.tick()
    return s, events_by_turn, coached


def session_metrics(s, ebt, coached):
    n_mist = sum(len(e) for e in ebt)
    half = N_TURNS // 2
    first = sum(len(e) for e in ebt[:half])
    second = sum(len(e) for e in ebt[half:])
    repeats = total = 0
    for turn, traits in coached:                       # turn = completed turns after this action
        for tr in traits:
            total += 1
            window = ebt[turn: turn + 3]
            if any(EVENT_TO_TRAIT[x] == tr for ev in window for x in ev):
                repeats += 1
    return {"mistakes": n_mist, "first_half": first, "second_half": second,
            "repeat_rate": (repeats / total) if total else None,
            "final_value": s.state()["value"],
            "mismatch_flagged": any(_codes(row) & PANIC_CODES for row in s.log),
            "any_mismatch_flagged": any(_codes(row) for row in s.log)}


def boot_ci(xs, n=2000, seed=0):
    rng = random.Random(seed)
    m = [stats.mean(rng.choices(xs, k=len(xs))) for _ in range(n)]
    m.sort()
    return stats.mean(xs), m[int(0.025 * n)], m[int(0.975 * n)]


def make_people(n, seed, blind_spot=0.0):
    rng = random.Random(seed)
    people = []
    for _ in range(n):
        p = Persona(random.Random(rng.random()))
        people.append((p, p.quiz_answers(blind_spot), rng.randrange(10**6)))
    return people


def estimation(people):
    """Quiz-only vs Bayesian (quiz prior + behaviour) trait estimates against persona truth."""
    top = lambda d: max(d, key=d.get)
    hit_q = hit_b = 0
    err_q, err_b = [], []
    for i, (p, ans, sd) in enumerate(people):
        s, *_ = play(p, ans, "none", sd, 0.0, f"p{i}")
        snap = s.um.snapshot()
        truth = top(p.true)
        hit_q += top(snap["quiz_traits"]) == truth
        hit_b += top(snap["long_term"]) == truth
        for k in TRAIT_KEYS:
            err_q.append(abs(snap["quiz_traits"][k] - p.true[k]))
            err_b.append(abs(snap["long_term"][k] - p.true[k]))
    n = len(people)
    return {"top_trait_acc_quiz_only": hit_q / n, "top_trait_acc_quiz_plus_behaviour": hit_b / n,
            "mae_quiz_only": stats.mean(err_q), "mae_quiz_plus_behaviour": stats.mean(err_b)}


def run(n=300, seed=7, rhos=(1.0, 1.5, 2.0), out="results"):
    os.makedirs(out, exist_ok=True)
    people = make_people(n, seed)

    # ---------- A1: mismatch detection (llm mode, heed irrelevant: use 'none' coaching) --------
    tp = fn = fp = tn = 0
    any_flag = 0
    for i, (p, ans, sd) in enumerate(people):
        s, ebt, co = play(p, ans, "none", sd, 0.0, f"p{i}")
        m = session_metrics(s, ebt, co)
        flagged = m["mismatch_flagged"]
        any_flag += m["any_mismatch_flagged"]
        if p.gt_mismatch:
            tp += flagged; fn += (not flagged)
        else:
            fp += flagged; tn += (not flagged)
    det = {"n_gt_mismatch": tp + fn, "n_personas": n, "recall": tp / max(1, tp + fn),
           "precision": tp / max(1, tp + fp),
           "false_positive_rate": fp / max(1, fp + tn),
           "share_sessions_with_any_mismatch_flag": any_flag / n}
    est = {"honest_quiz": estimation(people),
           "blind_spot_quiz": estimation(make_people(n, seed + 1, blind_spot=BLIND_SPOT))}

    # ---------- B: behavioural shift (assumed heed model; sweep rho = llm_heed / baseline_heed) ----
    rows, summary = [], {}
    for rho in rhos:
        heed_llm = min(0.95, HEED_BASE * rho)
        per = {"none": [], "baseline": [], "llm": []}
        for i, (p, ans, sd) in enumerate(people):
            for mode, heed in (("none", 0.0), ("baseline", HEED_BASE), ("llm", heed_llm)):
                s, ebt, co = play(p, ans, mode, sd, heed, f"p{i}")
                m = session_metrics(s, ebt, co)
                per[mode].append(m)
                rows.append({"rho": rho, "persona": i, "mode": mode, **m})
        res = {}
        for mode in ("none", "baseline", "llm"):
            res[mode] = {"mistakes_mean": stats.mean(x["mistakes"] for x in per[mode]),
                         "second_half_mean": stats.mean(x["second_half"] for x in per[mode]),
                         "repeat_rate_mean": stats.mean(x["repeat_rate"] for x in per[mode] if x["repeat_rate"] is not None)
                         if any(x["repeat_rate"] is not None for x in per[mode]) else None,
                         "final_value_mean": stats.mean(x["final_value"] for x in per[mode])}
        d = [b["mistakes"] - l["mistakes"] for b, l in zip(per["baseline"], per["llm"])]
        d2 = [b["second_half"] - l["second_half"] for b, l in zip(per["baseline"], per["llm"])]
        res["paired_baseline_minus_llm_mistakes"] = dict(zip(("mean", "ci_lo", "ci_hi"), boot_ci(d)))
        res["paired_baseline_minus_llm_second_half"] = dict(zip(("mean", "ci_lo", "ci_hi"), boot_ci(d2)))
        summary[str(rho)] = res

    # ---------- C: message grounding checks (offline generator) -------------------------------
    chk = {"messages": 0, "names_event_numbers": 0, "valid": 0}
    from .coach_llm import _valid
    for i, (p, ans, sd) in enumerate(people[:100]):
        s, *_ = play(p, ans, "llm", sd, 0.3, f"g{i}")
        for row in s.log:
            if row["coach_source"] not in ("not_triggered", "disabled", "cooldown"):
                for msg in row["coach_message"].split(" || "):
                    chk["messages"] += 1
                    chk["names_event_numbers"] += any(ch.isdigit() for ch in msg)
                    chk["valid"] += _valid(msg)
    chk["share_with_user_numbers"] = chk["names_event_numbers"] / max(1, chk["messages"])
    chk["share_valid"] = chk["valid"] / max(1, chk["messages"])

    result = {"n_personas": n, "seed": seed, "heed_baseline_assumed": HEED_BASE,
              "blind_spot_max_underreport": BLIND_SPOT,
              "detection": det, "estimation": est, "shift_sensitivity": summary, "grounding": chk}
    with open(os.path.join(out, "eval_summary.json"), "w") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(out, "eval_sessions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return result

# ---------------------------------------------------------------------------
# Exploratory analyses (run: python -m cognifin.evaluate --extra)
# ---------------------------------------------------------------------------
def extra_analyses(n=300, seed=7, out="results"):
    """(1) Mismatch detector: threshold sweep and 'at least k flagged turns' aggregation.
       (2) Trait estimation: quiz-only vs additive update vs population-normalised update.
    These are post-hoc, exploratory, and run on the same simulated personas as run()."""
    from . import mismatch as mm
    os.makedirs(out, exist_ok=True)
    people = make_people(n, seed)

    res = {"detector_sweep": [], "estimation": {}}
    orig = mm.HIGH
    try:
        for high in (0.6, 0.7, 0.8, 0.9):
            mm.HIGH = high
            flags = []
            for i, (p, ans, sd) in enumerate(people):
                s, ebt, co = play(p, ans, "none", sd, 0.0, f"p{i}")
                flags.append((p.gt_mismatch, sum(1 for r in s.log if _codes(r) & PANIC_CODES)))
            for k in (1, 2, 3):
                tp = sum(1 for g, c in flags if g and c >= k)
                fn = sum(1 for g, c in flags if g and c < k)
                fp = sum(1 for g, c in flags if (not g) and c >= k)
                tn = sum(1 for g, c in flags if (not g) and c < k)
                res["detector_sweep"].append({"threshold": high, "min_flagged_turns": k,
                    "recall": tp / max(1, tp + fn), "precision": tp / max(1, tp + fp),
                    "false_positive_rate": fp / max(1, fp + tn)})
    finally:
        mm.HIGH = orig

    # --- estimation ---
    from .simulator import N_TURNS  # noqa: F401
    ev_types = ["panic_sell", "fomo_buy", "overconcentration", "overtrading", "hold_loser", "early_profit_take"]
    rows = []
    for i, (p, ans, sd) in enumerate(people):
        s, ebt, co = play(p, ans, "none", sd, 0.0, f"p{i}")
        cnt = {e: sum(x.count(e) for x in ebt) for e in ev_types}
        sn = s.um.snapshot()
        rows.append((p, sn, cnt))
    mean_cnt = {e: max(1e-9, sum(r[2][e] for r in rows) / n) for e in ev_types}
    t_of = {"panic_sell": "panic_selling", "fomo_buy": "herding_fomo", "overconcentration": "overconfidence",
            "overtrading": "overconfidence", "hold_loser": "loss_aversion", "early_profit_take": "loss_aversion"}
    acc = {"quiz_only": 0, "bayesian_update": 0, "population_normalised": 0, "behaviour_only_normalised": 0}
    for p, sn, cnt in rows:
        truth = max(p.true, key=p.true.get)
        top = lambda d: max(d, key=d.get)
        acc["quiz_only"] += top(sn["quiz_traits"]) == truth
        acc["bayesian_update"] += top(sn["long_term"]) == truth
        rel = {k: 0.0 for k in sn["quiz_traits"]}
        for e in ev_types:
            rel[t_of[e]] += cnt[e] / mean_cnt[e]
        for k in rel:                      # average relative intensity over the trait's event types
            rel[k] /= sum(1 for e in ev_types if t_of[e] == k)
        beh = {k: v / (1 + v) for k, v in rel.items()}          # squash to [0, 1)
        comb = {k: 0.5 * sn["quiz_traits"][k] + 0.5 * beh[k] for k in beh}
        acc["population_normalised"] += top(comb) == truth
        acc["behaviour_only_normalised"] += top(beh) == truth
    res["estimation"] = {k: v / n for k, v in acc.items()}
    res["ablation_update_rule"] = ablation_update_rule(n, seed)
    with open(os.path.join(out, "extra_summary.json"), "w") as f:
        json.dump(res, f, indent=2)
    return res


def _legacy_additive_update(self, events, contexts):
    """The original v1 rule, kept only for the ablation: +0.15*(1-v) per fired trait,
    -0.075*v per resisted dip/rally, no opportunity counting for loss aversion."""
    fired = {EVENT_TO_TRAIT[e["type"]] for e in events}
    for t in fired:
        self.long_term[t] += 0.15 * (1 - self.long_term[t])
    for c, t in (("dip", "panic_selling"), ("rally", "herding_fomo")):
        if c in contexts and t not in fired:
            self.long_term[t] -= 0.075 * self.long_term[t]
    for k in self.long_term:
        self.long_term[k] = round(min(1.0, max(0.0, self.long_term[k])), 4)


def ablation_update_rule(n=300, seed=7):
    """Bayesian opportunity-based update vs the legacy additive event-count rule."""
    from .user_model import UserModel
    out = {}
    for label, blind in (("honest_quiz", 0.0), ("blind_spot_quiz", BLIND_SPOT)):
        sd = seed if blind == 0.0 else seed + 1
        out[label] = {"bayesian": estimation(make_people(n, sd, blind))}
        original = UserModel.update_long_term
        UserModel.update_long_term = _legacy_additive_update
        try:
            out[label]["legacy_additive"] = estimation(make_people(n, sd, blind))
        finally:
            UserModel.update_long_term = original
    return out


# ---------------------------------------------------------------------------
# Message-level comparison of the three coach generators on fixed scenarios
# (run: python -m cognifin.evaluate --llm-check; needs GEMINI_API_KEY for the LLM arm)
# ---------------------------------------------------------------------------
SCENARIO_EVENTS = [
    {"type": "panic_sell", "asset": "TECH", "drop_pct": -15.8, "loss_vs_cost_pct": -18.2},
    {"type": "fomo_buy", "asset": "TECH", "recent_gain_pct": 17.4},
    {"type": "overconcentration", "asset": "TECH", "weight_pct": 83},
    {"type": "overtrading", "trades_in_last_5": 5},
    {"type": "hold_loser", "asset": "INDEX", "loss_vs_cost_pct": -12.6, "turns": 3},
    {"type": "early_profit_take", "asset": "INDEX", "gain_pct": 3.4, "loser": "TECH"},
]
MISMATCH_FOR = {
    "panic_sell": {"code": "risk_claim_vs_panic", "claim": "are comfortable with high-risk investments",
                   "behaviour": "sold after a 15.8% drop, locking in a loss", "trait": "panic_selling"},
    "fomo_buy": {"code": "trend_claim_vs_fomo", "claim": "ignore what is trending",
                 "behaviour": "bought TECH after a 17.4% run-up", "trait": "herding_fomo"},
}


def _numbers(event):
    return [f"{abs(v):g}" for k, v in event.items() if isinstance(v, (int, float)) and k != "turns"]


def _scenario_key(r):
    return (r["event"], r["trait_prior"], r["mismatch_given"])


def llm_check(out="results", use_api=True, delay=7.0):
    """Compare generators on 24 fixed scenarios. Resumable: Gemini-written messages already in
    results/llm_check.json are kept, and the API is called only for scenarios still missing one.
    The "llm" summary is computed over messages actually written by the model (fallbacks are
    counted separately), so offline text is never reported as LLM output."""
    import time
    from . import coach_baseline, coach_llm
    from .user_model import UserModel
    path = os.path.join(out, "llm_check.json")
    done = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                for r in json.load(f).get("messages", []):
                    if r["generator"] == "llm" and r["source"] == "llm":
                        done[_scenario_key(r)] = r
        except (OSError, ValueError, KeyError):
            done = {}
    rows = []
    for intensity_level in (0.2, 0.8):
        for with_mismatch in (False, True):
            for ev in SCENARIO_EVENTS:
                trait = EVENT_TO_TRAIT[ev["type"]]
                um = UserModel("check", {k: 0.5 for k in TRAIT_KEYS} | {trait: intensity_level},
                               {"self_risk_tolerance": 0.75})
                um.update_short_term([ev], 0.12, 2500)
                mm = [MISMATCH_FOR[ev["type"]]] if with_mismatch and ev["type"] in MISMATCH_FOR else []
                gens = {"baseline": lambda: coach_baseline.coach(ev),
                        "offline": lambda: coach_llm.coach(ev, user_model=um, mismatches=mm, use_api=False)}
                key = (ev["type"], intensity_level, bool(mm))
                if key in done:
                    rows.append(done[key])
                elif use_api:
                    def _llm(ev=ev, um=um, mm=mm):
                        time.sleep(delay)                 # pace calls for free-tier quotas
                        return coach_llm.coach(ev, user_model=um, mismatches=mm, use_api=True)
                    gens["llm"] = _llm
                for name, g in gens.items():
                    t0 = time.time()
                    c = g()
                    dt = time.time() - t0 - (delay if name == "llm" else 0.0)
                    msg = c["message"]
                    rows.append({
                        "generator": name, "source": c["source"], "model": c.get("model"),
                        "event": ev["type"], "trait_prior": intensity_level, "mismatch_given": bool(mm),
                        "words": len(msg.split()), "valid": coach_llm._valid(msg),
                        "cites_event_number": any(n in msg for n in _numbers(ev)),
                        "mentions_mismatch": bool(mm) and any(w in msg.lower() for w in ("quiz", "said", "noted", "reported", "described", "mentioned", "claimed", "told")),
                        "has_why_this": c["why_this"] is not None,
                        "latency_s": round(dt, 2), "message": msg})

    def summarise(rs):
        if not rs:
            return {"n": 0}
        mm_rs = [r for r in rs if r["mismatch_given"]]
        return {"n": len(rs),
                "share_valid": stats.mean(r["valid"] for r in rs),
                "share_cites_event_number": stats.mean(r["cites_event_number"] for r in rs),
                "share_mentions_mismatch_when_given": stats.mean(r["mentions_mismatch"] for r in mm_rs) if mm_rs else None,
                "share_with_why_this": stats.mean(r["has_why_this"] for r in rs),
                "words_mean": stats.mean(r["words"] for r in rs),
                "distinct_messages": len({r["message"] for r in rs}),
                "latency_s_median": stats.median(r["latency_s"] for r in rs)}

    summary = {"baseline": summarise([r for r in rows if r["generator"] == "baseline"]),
               "offline": summarise([r for r in rows if r["generator"] == "offline"])}
    llm_rows = [r for r in rows if r["generator"] == "llm"]
    real = [r for r in llm_rows if r["source"] == "llm"]
    summary["llm"] = summarise(real) | {"scenarios": 24, "written_by_model": len(real),
                                        "fell_back": len(llm_rows) - len(real),
                                        "models": sorted({r["model"] for r in real if r.get("model")})}
    os.makedirs(out, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"summary": summary, "messages": rows}, f, indent=2)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="results")
    ap.add_argument("--extra", action="store_true", help="run exploratory detector/estimation analyses instead")
    ap.add_argument("--llm-check", action="store_true",
                    help="compare baseline / offline / Gemini messages on 24 fixed scenarios")
    a = ap.parse_args()
    if a.llm_check:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
        print(json.dumps(llm_check(a.out, use_api=bool(os.environ.get("GEMINI_API_KEY")
                                                        or os.environ.get("GOOGLE_API_KEY"))), indent=2))
    elif a.extra:
        print(json.dumps(extra_analyses(a.n, a.seed, out=a.out), indent=2))
    else:
        print(json.dumps(run(a.n, a.seed, out=a.out), indent=2))
