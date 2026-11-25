"""Self-report profiling quiz (Likert 1-5).

Items are short statements written for this prototype, inspired by constructs in the
behavioral-finance literature. They are NOT a validated psychometric instrument;
see README / paper (Limitations).
"""

# (id, text, construct, reverse_coded)
ITEMS = [
    # loss aversion
    ("la1", "A $100 loss bothers me much more than a $100 gain pleases me.", "loss_aversion", False),
    ("la2", "I find it hard to sell an investment that is below what I paid for it.", "loss_aversion", False),
    ("la3", "I would rather lock in a small profit now than wait for a bigger one.", "loss_aversion", False),
    # overconfidence
    ("oc1", "I am better than most people at picking winning investments.", "overconfidence", False),
    ("oc2", "I would put most of my money in one investment I strongly believe in.", "overconfidence", False),
    ("oc3", "Frequent trading is a good way to beat the market.", "overconfidence", False),
    # herding / FOMO
    ("hf1", "When an investment is rising fast, I worry about missing out.", "herding_fomo", False),
    ("hf2", "I feel more comfortable buying what many other people are buying.", "herding_fomo", False),
    ("hf3", "I usually ignore what is trending when deciding where to invest.", "herding_fomo", True),
    # panic selling
    ("ps1", "When prices fall quickly, I feel an urge to sell right away.", "panic_selling", False),
    ("ps2", "I stick to my plan even when the market drops sharply.", "panic_selling", True),
    ("ps3", "Watching my portfolio fall makes it hard for me to think clearly.", "panic_selling", False),
    # self-report of own behaviour (used for grounding against actual play)
    ("sr1", "I am comfortable with high-risk investments.", "self_risk_tolerance", False),
    ("sr2", "I stay calm when my investments lose value.", "self_calm_under_loss", False),
    ("sr3", "I rarely change my investments once I have made them.", "self_trades_rarely", False),
]

TRAIT_CONSTRUCTS = ["loss_aversion", "overconfidence", "herding_fomo", "panic_selling"]
SELF_CONSTRUCTS = ["self_risk_tolerance", "self_calm_under_loss", "self_trades_rarely"]


def get_quiz():
    return [{"id": i, "text": t} for i, t, _, _ in ITEMS]


def score_quiz(answers):
    """answers: {item_id: 1..5}. Returns {'traits': {...0..1}, 'self_report': {...0..1}}.

    Higher trait value = stronger bias tendency. Missing items default to neutral (3).
    """
    buckets = {}
    for item_id, _, construct, rev in ITEMS:
        a = answers.get(item_id, 3)
        try:
            a = int(a)
        except (TypeError, ValueError):
            a = 3
        a = min(5, max(1, a))
        if rev:
            a = 6 - a
        buckets.setdefault(construct, []).append((a - 1) / 4.0)
    mean = lambda xs: sum(xs) / len(xs)
    traits = {c: round(mean(buckets[c]), 3) for c in TRAIT_CONSTRUCTS}
    self_report = {c: round(mean(buckets[c]), 3) for c in SELF_CONSTRUCTS}
    return {"traits": traits, "self_report": self_report}
