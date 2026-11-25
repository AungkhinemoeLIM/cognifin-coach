"""Grounding self-report against behavioural evidence.

Flags cases where what the user *said* in the quiz conflicts with what they *did*.
Rationale: people readily see biases in others but not in themselves (the "bias blind
spot", Pronin, Lin & Ross, 2002), so self-report alone is an unreliable profile. Showing
a concrete claim-vs-behaviour contrast is a metacognitive prompt, not a verdict.
"""

HIGH = 0.7
LOW = 0.35


def detect_mismatches(self_report, quiz_traits, events):
    """Return a list of mismatch dicts for the events of the current turn."""
    out = []
    for e in events:
        t = e["type"]
        if t == "panic_sell":
            if self_report.get("self_risk_tolerance", 0) >= HIGH:
                out.append({"code": "risk_claim_vs_panic",
                            "claim": "are comfortable with high-risk investments",
                            "behaviour": f"sold after a {abs(e['drop_pct'])}% drop, locking in a loss",
                            "trait": "panic_selling"})
            if self_report.get("self_calm_under_loss", 0) >= HIGH:
                out.append({"code": "calm_claim_vs_panic",
                            "claim": "stay calm when investments lose value",
                            "behaviour": f"sold {e['asset']} quickly after a {abs(e['drop_pct'])}% drop",
                            "trait": "panic_selling"})
        elif t in ("overtrading",):
            if self_report.get("self_trades_rarely", 0) >= HIGH:
                out.append({"code": "patience_claim_vs_overtrading",
                            "claim": "rarely change your investments",
                            "behaviour": "traded on five consecutive turns",
                            "trait": "overconfidence"})
        elif t == "fomo_buy":
            if quiz_traits.get("herding_fomo", 1) <= LOW:
                out.append({"code": "trend_claim_vs_fomo",
                            "claim": "ignore what is trending",
                            "behaviour": f"bought {e['asset']} after a {e['recent_gain_pct']}% run-up",
                            "trait": "herding_fomo"})
        elif t == "overconcentration":
            if quiz_traits.get("overconfidence", 1) <= LOW:
                out.append({"code": "humble_claim_vs_concentration",
                            "claim": "would not put most of your money in one investment",
                            "behaviour": f"moved {e['weight_pct']}% of the portfolio into {e['asset']}",
                            "trait": "overconfidence"})
    return out
