"""Scripted end-to-end demo trace: perception -> inference -> output, turn by turn.

A backup for the live demo and a way to show the reasoning step in a terminal. A scripted
player claims to be calm and risk-tolerant and to ignore trends, then chases the rally and
panic-sells in the crash.

    python demo/trace_demo.py               # offline generator (no API key needed)
    python demo/trace_demo.py --llm         # use Gemini if GEMINI_API_KEY is set in .env
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from cognifin.knowledge import TRAIT_KEYS        # noqa: E402
from cognifin.session import Session             # noqa: E402

SEED = 42
# quiz: strong self-claims of calm / risk tolerance, low stated herding
ANSWERS = {"la1": 3, "la2": 3, "la3": 3, "oc1": 2, "oc2": 2, "oc3": 2,
           "hf1": 2, "hf2": 1, "hf3": 5, "ps1": 2, "ps2": 4, "ps3": 2,
           "sr1": 5, "sr2": 5, "sr3": 4}


def turn_plan(t):
    """(decisions for BOND/INDEX/TECH, decision_ms, reason)."""
    hold = {"BOND": ("hold", 0), "INDEX": ("hold", 0), "TECH": ("hold", 0)}
    if t == 0:
        hold.update(INDEX=("buy", 0.4), TECH=("buy", 0.2)); return hold, 9000, "following_plan"
    if t == 5:                                     # chase the rally
        hold.update(TECH=("buy", 0.6)); return hold, 3100, "reacting_to_price_change"
    if t == 12:                                    # crash: dump TECH fast
        hold.update(TECH=("sell", 1.0)); return hold, 2200, "reacting_to_price_change"
    return hold, 6500, None


def fmt_traits(um):
    return "  ".join(f"{k.split('_')[0][:6]:>6} {um.long_term[k]:.2f}±{um.uncertainty(k):.2f}"
                     for k in TRAIT_KEYS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="call Gemini (needs GEMINI_API_KEY)")
    a = ap.parse_args()
    if a.llm:
        sys.path.insert(0, ROOT)
        from app import load_dotenv
        load_dotenv(os.path.join(ROOT, ".env"))
    s = Session("demo", ANSWERS, coach_mode="llm", seed=SEED, use_api=a.llm, persist=False,
                plan="pause before reacting to a price drop")
    print("=" * 96)
    print("PERCEPTION  quiz ->", {k: round(v, 2) for k, v in s.um.quiz_traits.items()})
    print("            self-claims ->", s.um.self_report)
    print("INFERENCE   prior   ", fmt_traits(s.um))
    print("=" * 96)
    while s.turn < 20:
        plan, ms, reason = turn_plan(s.turn)
        acts = [{"type": typ, "asset": asset, "fraction": frac} for asset, (typ, frac) in plan.items()]
        px = s.px()
        r = s.step(acts, ms, reason)
        traded = [f"{x['type']} {x['asset']} {x['fraction']:.0%}" for x in acts if x["type"] != "hold"]
        if not (r["events"] or r["observations"] or traded):
            continue
        print(f"\nturn {s.turn:2d} | prices B {px['BOND']:.1f}  I {px['INDEX']:.1f}  T {px['TECH']:.1f}"
              f" | action: {', '.join(traded) or 'hold all'} | {ms / 1000:.1f}s")
        for o in r["observations"]:
            print(f"   perception  observation: {o['description']}")
        for e in r["events"]:
            print(f"   perception  EVENT {e['type']}: { {k: v for k, v in e.items() if k != 'type'} }")
        for m in r["mismatches"]:
            print(f"   inference   MISMATCH: claimed you {m['claim']} / did: {m['behaviour']}")
        print(f"   inference   posterior {fmt_traits(s.um)}")
        st = s.um.short_term
        print(f"   inference   short-term: drawdown {st['drawdown']:.1%}, hasty={st['hasty']}")
        for c in r["coaching"]:
            w = c["why_this"]
            print(f"   output      [{c['source']}] {c['message']}")
            print(f"   output      why-this: {w['event_evidence']} | {w['profile_note'][:110]}...")
            print(f"               source: {w['citation']} | reflect: {w['reflection_question']}")
    print("\n" + "=" * 96)
    print("SUMMARY", s.summary()["event_counts"], "| final value", s.state()["value"])


if __name__ == "__main__":
    main()
