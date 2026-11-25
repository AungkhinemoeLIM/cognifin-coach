"""Baseline: static, template-based rule coach (same advice for every user)."""
from .knowledge import EVENT_TO_TRAIT

TEMPLATES = {
    "panic_sell": "Prices fell and you sold. Remember that markets fluctuate; avoid selling in a hurry.",
    "fomo_buy": "This asset has risen recently. Be careful about chasing past performance.",
    "overconcentration": "Your portfolio is concentrated in one asset. Diversification reduces risk.",
    "overtrading": "You have been trading a lot. Frequent trading can increase costs.",
    "hold_loser": "One of your holdings has lost value for several turns. Review whether to keep it.",
    "early_profit_take": "You sold a small gain while holding a loser. Consider your overall plan.",
}


def coach(event, **_ignored):
    """Return a coach message dict for one event. Ignores the user profile by design."""
    return {
        "mode": "baseline",
        "event_type": event["type"],
        "trait": EVENT_TO_TRAIT[event["type"]],
        "message": TEMPLATES[event["type"]],
        "source": "rule-template",
        "why_this": None,                  # baseline offers no explanation panel
    }
