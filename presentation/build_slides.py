"""Build the 16:9 presentation deck (PDF) for the CPE 663 class presentation.

Run from the project root:  python presentation/build_slides.py
Output: presentation/CogniFin_Coach_Slides.pdf   (speaker notes: presentation/SPEAKER_NOTES.md)
Numbers are read from results/ and author details from paper/author.json.
"""
import json
import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "paper"))
import content  # noqa: E402

FIG = os.path.join(ROOT, "paper", "figures")
OUT = os.path.join(ROOT, "presentation", "CogniFin_Coach_Slides.pdf")
W, H = 960, 540

NAVY, INK, MUTE = HexColor("#1E2761"), HexColor("#1F2430"), HexColor("#5F6470")
ORANGE, BLUE, AQUA, AMBER = HexColor("#EB6834"), HexColor("#2A78D6"), HexColor("#1BAF7A"), HexColor("#EDA100")
TINT, LINE, WHITE, ICE = HexColor("#F3F5FA"), HexColor("#DDE1EA"), HexColor("#FFFFFF"), HexColor("#CADCFC")

FD = "/System/Library/Fonts/Supplemental/"
for n, f in (("Sans", "Arial.ttf"), ("Sans-B", "Arial Bold.ttf"), ("Sans-I", "Arial Italic.ttf"),
             ("Serif-B", "Times New Roman Bold.ttf"), ("Serif", "Times New Roman.ttf"),
             ("Mono", "Courier New.ttf")):
    pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-B")


def para(c, text, x, y_top, w, size=15, color=INK, leading=None, font="Sans", align=0):
    st = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading or size * 1.3,
                        textColor=color, alignment=align)
    p = Paragraph(text, st)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def title(c, text, kicker=None):
    c.setFillColor(WHITE); c.rect(0, 0, W, H, stroke=0, fill=1)
    if kicker:
        c.setFillColor(ORANGE); c.setFont("Sans-B", 11); c.drawString(48, H - 46, kicker.upper())
    c.setFillColor(NAVY); c.setFont("Serif-B", 31); c.drawString(48, H - 82, text)


def footer(c, n, dark=False):
    c.setFont("Sans", 9); c.setFillColor(ICE if dark else MUTE)
    c.drawString(48, 22, "CogniFin Coach · CPE 663 Cognitive Computing")
    c.drawRightString(W - 48, 22, str(n))


def card(c, x, y, w, h, fill=TINT, radius=10):
    c.setFillColor(fill); c.setStrokeColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=0, fill=1)


def dot(c, x, y, r, color, label=None):
    c.setFillColor(color); c.circle(x, y, r, stroke=0, fill=1)
    if label:
        c.setFillColor(WHITE); c.setFont("Sans-B", r * 1.05); c.drawCentredString(x, y - r * 0.36, label)


def image(c, name, x, y, w=None, h=None):
    r = ImageReader(os.path.join(FIG, name + ".png"))
    iw, ih = r.getSize()
    if w and not h:
        h = w * ih / iw
    elif h and not w:
        w = h * iw / ih
    c.drawImage(r, x, y, width=w, height=h, mask="auto")
    return w, h


def stat(c, x, y, value, label, color=NAVY, w=200):
    c.setFillColor(color); c.setFont("Serif-B", 40); c.drawString(x, y, value)
    para(c, label, x, y - 8, w, size=12.5, color=MUTE)


def example_panic():
    """A real panic-sell message from results/llm_check.json (prefer one written by Gemini) and
    the matching "Why this?" panel computed by the app's own code for the same scenario."""
    sys.path.insert(0, ROOT)
    from cognifin.coach_llm import why_this
    from cognifin.evaluate import MISMATCH_FOR, SCENARIO_EVENTS
    from cognifin.knowledge import TRAIT_KEYS
    from cognifin.user_model import UserModel
    with open(os.path.join(ROOT, "results", "llm_check.json")) as f:
        rows = json.load(f)["messages"]
    cand = [r for r in rows if r["event"] == "panic_sell" and r["mismatch_given"]
            and r["generator"] in ("llm", "offline")]
    cand.sort(key=lambda r: (r["source"] != "llm", -r["trait_prior"]))
    row = cand[0]
    ev = next(e for e in SCENARIO_EVENTS if e["type"] == "panic_sell")
    um = UserModel("check", {k: 0.5 for k in TRAIT_KEYS} | {"panic_selling": row["trait_prior"]},
                   {"self_risk_tolerance": 0.75})
    um.update_short_term([ev], 0.12, 2500)
    return row["message"], why_this(um, ev, [MISMATCH_FOR["panic_sell"]]), row["source"]


def main():
    with open(os.path.join(ROOT, "paper", "author.json")) as f:
        author = json.load(f)
    author["repo_url"] = author["repo_url"].strip().removesuffix(".git")   # display form
    R = content.numbers()
    Hq, Bq = R["honest_quiz"], R["blind_spot_quiz"]
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("CogniFin Coach – class presentation"); c.setAuthor(author["name"])
    n = 0

    # 1 ---------------------------------------------------------------- title
    n += 1
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    for i, col in enumerate((BLUE, ORANGE, AQUA, AMBER)):
        dot(c, 64 + i * 30, 420, 9, col)
    c.setFillColor(WHITE); c.setFont("Serif-B", 58); c.drawString(48, 330, "CogniFin Coach")
    para(c, "A cognitive-profile-aware financial decision coach with Bayesian bias modelling and "
            "self-report grounding", 48, 312, 760, size=21, color=ICE)
    c.setFillColor(ORANGE); c.setFont("Sans-B", 14)
    c.drawString(48, 196, "PERCEIVE  ·  MODEL  ·  REASON  ·  EXPLAIN")
    para(c, f"<b>{author['name']}</b> &nbsp;·&nbsp; {author['student_id']}<br/>{author['course']}<br/>"
            f"{author['institution']}", 48, 160, 700, size=13, color=ICE)
    footer(c, n, dark=True); c.showPage()

    # 2 ---------------------------------------------------------------- problem
    n += 1
    title(c, "Investors repeat the same emotional mistakes", "Problem statement")
    biases = [("Panic selling", "sells right after a sharp drop, locking in the loss", "Kahneman 2011; Loewenstein 1996", ORANGE),
              ("Herding / FOMO", "buys what already ran up because others are profiting", "Banerjee 1992; Bikhchandani 1992", AMBER),
              ("Overconfidence", "trades too often, bets too much on one asset", "Barber & Odean 2000, 2001", BLUE),
              ("Loss aversion", "rides losers, cashes small winners early", "Tversky & Kahneman 1992; Odean 1998", AQUA)]
    for i, (t, d, src, col) in enumerate(biases):
        x = 48 + i * 218
        card(c, x, 196, 200, 220)
        dot(c, x + 30, 384, 13, col)
        c.setFillColor(INK); c.setFont("Sans-B", 17); c.drawString(x + 18, 340, t)
        para(c, d, x + 18, 328, 168, size=14, color=INK)
        para(c, src, x + 18, 238, 168, size=10.5, color=MUTE)
    c.setFillColor(NAVY); c.setFont("Serif-B", 44); c.drawString(48, 120, "0.1%")
    para(c, "of the variance in financial behaviour is explained by financial-literacy training, and the "
            "effect decays within months (Fernandes et al., 2014). <b>Knowing the rule does not change the "
            "decision in the moment.</b>", 180, 160, 730, size=15, color=INK)
    footer(c, n); c.showPage()

    # 3 ---------------------------------------------------------------- cognitive motivation
    n += 1
    title(c, "Cognitive motivation shapes every design choice", "Why a cognitive system")
    cols = [("Fast thinking under stress", "Losses and time pressure hand control to System-1 and visceral states.",
             "Kahneman 2011 · Loewenstein 1996", "Short-term context: drawdown + hasty (< 4 s) decisions", BLUE),
            ("The bias blind spot", "People see biases in others, not in themselves, so self-report is unreliable.",
             "Pronin, Lin & Ross 2002", "Bayesian fusion of quiz + behaviour, and a mismatch detector", ORANGE),
            ("Metacognition & debiasing", "Timely, specific, personal feedback can reduce biased judgement.",
             "Flavell 1979 · Morewedge et al. 2015", "“Why this?” evidence + a reflection question, not advice", AQUA)]
    for i, (t, d, src, design, col) in enumerate(cols):
        x = 48 + i * 292
        card(c, x, 236, 272, 190)
        dot(c, x + 28, 396, 12, col, str(i + 1))
        c.setFillColor(INK); c.setFont("Sans-B", 17); c.drawString(x + 50, 390, t)
        para(c, d, x + 20, 366, 236, size=14.5)
        para(c, src, x + 20, 270, 236, size=10.5, color=MUTE)
        c.setStrokeColor(col); c.setLineWidth(2); c.line(x + 136, 228, x + 136, 196)
        c.setFillColor(col); p = c.beginPath(); p.moveTo(x + 130, 200); p.lineTo(x + 142, 200); p.lineTo(x + 136, 190)
        c.drawPath(p, stroke=0, fill=1)
        card(c, x, 92, 272, 92, fill=HexColor("#FFFFFF"))
        c.setStrokeColor(LINE); c.setLineWidth(1); c.roundRect(x, 92, 272, 92, 10, stroke=1, fill=0)
        c.setFillColor(col); c.setFont("Sans-B", 10.5); c.drawString(x + 20, 162, "DESIGN RESPONSE")
        para(c, design, x + 20, 154, 236, size=14.5, color=INK)
    footer(c, n); c.showPage()

    # 4 ---------------------------------------------------------------- architecture
    n += 1
    title(c, "Four-layer architecture in a closed perception–action loop", "System architecture")
    iw, _ = image(c, "fig_architecture", 0, 0, h=0.001) if False else (None, None)
    r = ImageReader(os.path.join(FIG, "fig_architecture.png")); aw, ah = r.getSize()
    hh = 330; ww = hh * aw / ah
    image(c, "fig_architecture", (W - ww) / 2, 100, w=ww, h=hh)
    para(c, "Each of 20 turns: perceive the decision → update the user model → generate a validated message → "
            "explain it deterministically. The LLM never writes the evidence or the citation.",
         48, 82, W - 96, size=13, color=MUTE)
    footer(c, n); c.showPage()

    # 5 ---------------------------------------------------------------- Bayesian model
    n += 1
    title(c, "A Bayesian user model that knows how sure it is", "Core mechanic 1 · long-term layer")
    card(c, 48, 286, 400, 128)
    para(c, "θ ~ Beta( n<sub>0</sub>q + F ,  n<sub>0</sub>(1 − q) + R )", 66, 402, 370, size=21,
         color=NAVY, font="Serif")
    c.setFont("Sans", 12.5); c.setFillColor(MUTE)
    c.drawString(66, 350, "q = quiz score (prior)     F = bias fired     R = resisted")
    c.drawString(66, 330, "estimate = posterior mean,  shown ± posterior SD")
    c.drawString(66, 310, "evidence carried across sessions at 0.5")
    bl = [("n<sub>0</sub> = 24 is derived, not tuned:", "a 3-item quiz has SE ≈ 0.10, worth ~24 observations."),
          ("Count opportunities, not just events:", "FOMO fires 66× more often than early profit-taking; "
           "the old “+0.15 per event” rule inflated noisy traits."),
          ("Overconfidence is confirm-only:", "it has no well-defined “resisted” situation.")]
    y = 262
    for b, t in bl:
        h = para(c, f"<b>{b}</b> {t}", 48, y, 400, size=14)
        y -= h + 12
    image(c, "fig_trajectory", 476, 150, w=436)
    para(c, "One under-reporting, panic-prone persona over three sessions: the estimate moves with each "
            "panic sale and its band narrows, but slowly (stable, not plastic).", 476, 140, 436, size=11.5, color=MUTE)
    footer(c, n); c.showPage()

    # 6 ---------------------------------------------------------------- grounded coaching
    n += 1
    title(c, "Grounded coaching: the LLM writes words, code writes facts", "Core mechanic 2 · generation")
    steps = [("Structured prompt", "event + numbers, bias hypothesis, intensities, haste, drawdown, ± SD, mismatch", BLUE),
             ("Gemini 3 Flash", "2–3 sentences, ≤ 70 words, no advice, no predictions, low thinking level", AQUA),
             ("Validator", "rejects truncation, > 110 words, “guaranteed”, “will recover”, “you should buy”", AMBER),
             ("Labelled fallback", "offline generator from the same inputs; source tag in UI and log", ORANGE)]
    y = 418
    for i, (t, d, col) in enumerate(steps):
        dot(c, 66, y - 12, 13, col, str(i + 1))
        c.setFillColor(INK); c.setFont("Sans-B", 15); c.drawString(92, y - 17, t)
        para(c, d, 92, y - 24, 330, size=12.5, color=MUTE)
        y -= 78
    msg, why, src = example_panic()
    card(c, 470, 92, 442, 340)
    c.setFillColor(ORANGE); c.setFont("Sans-B", 10.5)
    c.drawString(490, 408, "COACH MESSAGE · " + ("LLM (GEMINI)" if src == "llm" else "OFFLINE GENERATOR"))
    h = para(c, "“" + msg + "”", 490, 398, 402, size=12, font="Sans-I", leading=15)
    y = 398 - h - 16
    c.setFillColor(BLUE); c.setFont("Sans-B", 10.5); c.drawString(490, y, "WHY THIS?  (assembled by code)")
    para(c, f"<b>Rule noticed:</b> {why['event_evidence']}<br/>"
            f"<b>Profile:</b> quiz {why['quiz_score']:.0%} → estimate {why['trait_score']:.0%} ± "
            f"{why['trait_uncertainty']:.0%} ({why['intensity']})<br/>"
            f"<b>Reflection check:</b> you reported that you {why['mismatches'][0]['claimed']}<br/>"
            f"<b>Source:</b> {why['citation']}<br/>"
            f"<b>Consider:</b> {why['reflection_question']}",
         490, y - 8, 402, size=11.5, leading=15)
    footer(c, n); c.showPage()

    # 7 ---------------------------------------------------------------- demo
    n += 1
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.setFont("Sans-B", 11); c.drawString(48, H - 46, "LIVE DEMO · 90 SECONDS")
    c.setFillColor(WHITE); c.setFont("Serif-B", 31); c.drawString(48, H - 82, "From a decision to an explanation")
    blocks = [("1", "Input & perception", "Quiz → trait bars. Claim to be calm. Chase the TECH rally (turns 4–6) "
               "and watch the buy-after-rise observation and the FOMO event.", BLUE),
              ("2", "Inference", "In the crash (turns 12–13) sell TECH fast. Panic event + hasty flag + "
               "drawdown; reflection check fires; trait bar moves, ± SD narrows.", ORANGE),
              ("3", "Output & evaluation", "LLM message with source tag, open “Why this?”, rate 1–5, "
               "finish → process recap → download CSV log.", AQUA)]
    for i, (k, t, d, col) in enumerate(blocks):
        x = 48 + i * 292
        card(c, x, 150, 272, 250, fill=HexColor("#28336F"))
        dot(c, x + 32, 364, 16, col, k)
        c.setFillColor(WHITE); c.setFont("Sans-B", 18); c.drawString(x + 60, 357, t)
        para(c, d, x + 22, 326, 232, size=14.5, color=ICE)
    c.setFillColor(ICE); c.setFont("Mono", 14)
    c.drawString(48, 104, "python app.py  →  http://localhost:8000/?seed=42")
    c.setFont("Sans", 12); c.drawString(48, 80, "Backup if the network or API fails:  python demo/trace_demo.py   "
                                                 "(terminal trace of perception → inference → output)")
    footer(c, n, dark=True); c.showPage()

    # 8 ---------------------------------------------------------------- results 1
    n += 1
    title(c, "Behaviour improves the profile once evidence is counted right", "Key results · RQ1 & RQ2")
    image(c, "fig_estimation", 48, 120, w=470)
    para(c, f"{R['n']} simulated personas, paired design. Legacy = the original “+0.15 per event” rule.",
         48, 112, 470, size=11.5, color=MUTE)
    stat(c, 560, 380, f"{Hq['bayes_acc']:.3f}", f"top-trait accuracy vs. {Hq['quiz_acc']:.3f} quiz-only and "
                                                 f"{Hq['legacy_acc']:.3f} legacy (honest quiz)", BLUE, 350)
    stat(c, 560, 280, f"{Bq['bayes_acc']:.3f}", f"vs. {Bq['quiz_acc']:.3f} quiz-only when the quiz under-reports "
                                                 f"bias (blind spot); MAE {Bq['quiz_mae']:.3f} → {Bq['bayes_mae']:.3f}", BLUE, 350)
    stat(c, 560, 180, f"{R['recall']:.2f} / {R['precision']:.2f}", f"mismatch detector recall / precision; "
                      f"requiring 2 flagged turns gives precision {R['k2']['precision']:.2f}", ORANGE, 350)
    footer(c, n); c.showPage()

    # 9 ---------------------------------------------------------------- results 2
    n += 1
    title(c, "Grounded messages; benefit hinges on being heeded", "Key results · RQ3 & RQ4")
    image(c, "fig_messages", 48, 150, w=420)
    image(c, "fig_shift", 492, 150, w=420)
    L = R["llm"]
    ll = (L or {}).get("llm") or {}
    if ll.get("n"):
        para(c, f"24 fixed scenarios. Gemini wrote {ll['n']}/24 (rest hit quota → labelled fallback); it cites "
                f"the user’s numbers in {ll['share_cites_event_number']:.0%}, {ll['share_valid']:.0%} pass the "
                f"validator. Rule templates: 0%.", 48, 140, 420, size=12, color=INK)
    else:
        para(c, f"24 fixed scenarios. Offline generator cites the user’s numbers in "
                f"{L['offline']['share_cites_event_number']:.0%}; rule templates 0%. Live LLM arm pending "
                f"(API quota) — rerun --llm-check.", 48, 140, 420, size=12, color=INK)
    s20 = R["shift"]["2.0"]["paired_baseline_minus_llm_mistakes"]
    para(c, f"If the personalised coach is heeded 2× as often, bias events drop by {s20['mean']:.2f} "
            f"events/session [{s20['ci_lo']:.2f}, {s20['ci_hi']:.2f}] vs. the rule baseline. At 1× they are identical.",
         492, 140, 420, size=12, color=INK)
    card(c, 48, 52, W - 96, 34, fill=HexColor("#FDEBE3"))
    c.setFillColor(ORANGE); c.setFont("Sans-B", 12.5)
    c.drawString(64, 64, "Caveat: simulated personas, not people. These numbers verify the pipeline and bound "
                         "the effect; they do not show the coach helps humans.")
    footer(c, n); c.showPage()

    # 10 --------------------------------------------------------------- lessons
    n += 1
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.setFont("Sans-B", 11); c.drawString(48, H - 46, "LESSONS LEARNED & CONCLUSION")
    c.setFillColor(WHITE); c.setFont("Serif-B", 31); c.drawString(48, H - 82, "What we learned building it")
    lessons = [("Count opportunities, not events.", "The additive update made the profile worse; a Beta–Bernoulli "
                "model with a reliability-derived prior fixed it.", BLUE),
               ("Silent fallbacks hide failures.", "Gemini 3 thinking tokens (~550) exceeded the old 220-token cap: "
                "replies came back empty or truncated, and the “LLM” coach quietly became the template. A string "
                "“none” made every session count as flagged.", ORANGE),
               ("Separate facts from fluency.", "Evidence and citations from code, words from the LLM: zero "
                "hallucinated citations by construction.", AQUA),
               ("Stability vs. plasticity.", "A trustworthy prior learns slowly; a human study must decide the "
                "right speed, and whether personalisation is heeded more.", AMBER)]
    for i, (t, d, col) in enumerate(lessons):
        x = 48 + (i % 2) * 438
        y = 400 - (i // 2) * 150
        dot(c, x + 14, y - 8, 9, col)
        c.setFillColor(WHITE); c.setFont("Sans-B", 17); c.drawString(x + 34, y - 14, t)
        para(c, d, x + 34, y - 24, 380, size=14, color=ICE)
    c.setFillColor(ORANGE); c.setFont("Sans-B", 15)
    c.drawString(48, 84, "Next: a randomised study (personalised vs. rule vs. none), already built into the app.")
    c.setFillColor(ICE); c.setFont("Sans", 12); c.drawString(48, 60, "Thank you · Questions?   " + author["repo_url"])
    footer(c, n, dark=True); c.showPage()

    c.save()
    print(f"{n} slides -> {OUT}")


if __name__ == "__main__":
    main()
