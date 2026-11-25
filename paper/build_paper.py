"""Build the conference paper in two forms from one source (paper/content.py):

  paper/CogniFin_Coach_IEEE.tex  - IEEEtran conference LaTeX (compile on Overleaf or any TeX
                                   install: pdflatex CogniFin_Coach_IEEE.tex, twice)
  paper/CogniFin_Coach_IEEE.pdf  - two-column IEEE-layout PDF rendered with ReportLab, so a
                                   PDF exists even on machines without LaTeX

Run from the project root:  python paper/build_paper.py
Author details come from paper/author.json.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content  # noqa: E402

FIG = os.path.join(HERE, "figures")

# ----------------------------------------------------------------------------- markup
TOKEN = re.compile(r"(</?(?:i|b|tt|sub|super)>|\{c:[^}]+\})")


def cite_order(doc):
    order = []
    texts = [doc["abstract"]] + [str(b) for b in doc["body"]]
    for t in texts:
        for m in re.finditer(r"\{c:([^}]+)\}", t):
            for k in m.group(1).split(","):
                k = k.strip()
                if k not in order:
                    order.append(k)
    return order


# --- LaTeX -------------------------------------------------------------------------
TEX_UNI = {
    "—": "---", "–": "--", "“": "``", "”": "''", "‘": "`", "’": "'", "…": "\\ldots{}",
    "±": "\\ensuremath{\\pm}", "×": "\\ensuremath{\\times}", "≥": "\\ensuremath{\\geq}",
    "≤": "\\ensuremath{\\leq}", "≈": "\\ensuremath{\\approx}", "→": "\\ensuremath{\\rightarrow}",
    "←": "\\ensuremath{\\leftarrow}", "∈": "\\ensuremath{\\in}", "∪": "\\ensuremath{\\cup}",
    "∧": "\\ensuremath{\\wedge}", "¬": "\\ensuremath{\\neg}", "∅": "\\ensuremath{\\emptyset}",
    "√": "\\ensuremath{\\surd}", "α": "\\ensuremath{\\alpha}", "β": "\\ensuremath{\\beta}",
    "γ": "\\ensuremath{\\gamma}", "ρ": "\\ensuremath{\\rho}", "σ": "\\ensuremath{\\sigma}",
    "θ": "\\ensuremath{\\theta}", "Δ": "\\ensuremath{\\Delta}", "λ": "\\ensuremath{\\lambda}",
    "μ": "\\ensuremath{\\mu}", "ε": "\\ensuremath{\\varepsilon}", "θ̂": "\\ensuremath{\\hat\\theta}",
    "·": "\\ensuremath{\\cdot}", "é": "\\'e", "−": "\\ensuremath{-}",
}
TEX_TAG = {"<i>": "\\textit{", "<b>": "\\textbf{", "<tt>": "\\texttt{",
           "<sub>": "\\textsubscript{", "<super>": "\\textsuperscript{"}


def tex_text(s):
    s = (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
         .replace("$", "\\$").replace("#", "\\#").replace("_", "\\_").replace("{", "\\{")
         .replace("}", "\\}").replace("~", "\\textasciitilde{}").replace("^", "\\^{}")
         .replace("<", "\\textless{}").replace(">", "\\textgreater{}"))
    s = s.replace("θ̂", TEX_UNI["θ̂"])
    out = "".join(TEX_UNI.get(ch, ch) for ch in s)
    bad = [ch for ch in out if ord(ch) > 127]
    if bad:
        raise ValueError(f"unmapped characters for LaTeX: {sorted(set(bad))}")
    return out


def tex(s):
    out = []
    for tok in TOKEN.split(s):
        if not tok:
            continue
        if tok in TEX_TAG:
            out.append(TEX_TAG[tok])
        elif tok.startswith("</"):
            out.append("}")
        elif tok.startswith("{c:"):
            out.append("~\\cite{" + ",".join(k.strip() for k in tok[3:-1].split(",")) + "}")
        else:
            out.append(tex_text(tok))
    return re.sub(r"\s+~\\cite", "~\\\\cite", "".join(out))


def build_tex(doc, author, path):
    L = [r"\documentclass[conference]{IEEEtran}",
         r"\IEEEoverridecommandlockouts",
         r"\usepackage[T1]{fontenc}", r"\usepackage{cite}", r"\usepackage{amsmath,amssymb}", r"\usepackage{graphicx}",
         r"\usepackage{array}", r"\usepackage{url}", r"\usepackage[hidelinks]{hyperref}",
         r"\graphicspath{{figures/}}",
         r"\begin{document}",
         r"\title{" + tex(doc["title"]) + "}",
         r"\author{\IEEEauthorblockN{" + tex(author["name"]) + r"}" +
         r"\IEEEauthorblockA{\textit{" + tex(author["department"]) + r"} \\ " +
         r"\textit{" + tex(author["institution"]) + r"}\\ " + tex(author["location"]) + r" \\ " +
         r"Student ID: " + tex(author["student_id"]) + r" \quad " + tex(author["email"]) + r"}}",
         r"\maketitle",
         r"\begin{abstract}", tex(doc["abstract"]), r"\end{abstract}",
         r"\begin{IEEEkeywords}", tex(doc["keywords"]), r"\end{IEEEkeywords}", ""]
    first_section = True
    for b in doc["body"]:
        kind = b[0]
        if kind == "h1":
            L.append(r"\section{" + tex(b[1]) + "}")
            if first_section:
                first_section = False
            if b[1].startswith("System Architecture"):
                L += [r"\begin{figure*}[t]", r"\centering",
                      r"\includegraphics[width=\textwidth]{fig_architecture.pdf}",
                      r"\caption{CogniFin Coach architecture. Perception turns quiz answers and decisions "
                      r"into trait priors, events and opportunity contexts; the dual-layer user model, "
                      r"mismatch detector and knowledge base perform inference; the coach generates a "
                      r"validated message while ``Why this?'' is assembled deterministically; the user's "
                      r"next decision closes the loop.}",
                      r"\label{fig:arch}", r"\end{figure*}"]
        elif kind == "h2":
            L.append(r"\subsection{" + tex(b[1]) + "}")
        elif kind == "p":
            L.append(tex(b[1]) + "\n")
        elif kind == "bullets":
            L.append(r"\begin{itemize}")
            L += [r"\item " + tex(x) for x in b[1]]
            L.append(r"\end{itemize}")
        elif kind == "eq":
            L += [r"\begin{equation}", b[1], r"\end{equation}"]
        elif kind == "fig":
            L += [r"\begin{figure}[t]", r"\centering",
                  r"\includegraphics[width=\columnwidth]{" + b[1] + ".pdf}",
                  r"\caption{" + tex(b[2]) + "}", r"\label{fig:" + b[1] + "}", r"\end{figure}"]
        elif kind == "table":
            _, cap, head, rows, widths = b
            cols = "".join(r">{\raggedright\arraybackslash}p{" + f"{w * 0.93:.3f}" + r"\columnwidth}"
                           for w in widths)
            L += [r"\begin{table}[t]", r"\caption{" + tex(cap) + "}", r"\centering", r"\footnotesize",
                  r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{" + cols + "}", r"\hline",
                  " & ".join(r"\textbf{" + tex(h) + "}" for h in head) + r" \\ \hline"]
            L += [" & ".join(tex(c) for c in r) + r" \\" for r in rows]
            L += [r"\hline", r"\end{tabular}", r"\end{table}"]
        elif kind == "alg":
            _, title, lines = b
            L += [r"\begin{figure}[t]", r"\centering", r"\fbox{\begin{minipage}{0.95\columnwidth}",
                  r"\footnotesize\textbf{" + tex(title) + r"}\\[2pt]"]
            for n, (ind, t) in enumerate(lines, 1):
                L.append(r"{\scriptsize " + str(n) + r":}\hspace{" + f"{0.6 + ind * 1.2:.1f}" + r"em}" +
                         tex(t) + r"\\")
            L += [r"\end{minipage}}", r"\end{figure}"]
    L += [r"\section*{Acknowledgment}",
          "Prepared for " + tex(author["course"]) + ". Evaluation results use simulated personas only; "
          "no human-subject data were collected.", ""]
    L.append(r"\begin{thebibliography}{99}")
    refs = dict(doc["references"])
    for k in cite_order(doc):
        L.append(r"\bibitem{" + k + "} " + tex(refs[k]))
    L.append(r"\end{thebibliography}")
    L += [r"\appendices", r"\section{Code Repository and Reproduction}"]
    for kind, val in doc["appendix"]:
        if kind == "p":
            L.append(tex(val).replace(tex(author["repo_url"]), r"\url{" + author["repo_url"] + "}") + "\n")
        else:
            L += [r"\begin{verbatim}"] + val + [r"\end{verbatim}"]
    L.append(r"\end{document}")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


# --- ReportLab PDF -----------------------------------------------------------------
def build_pdf(doc, author, path):
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak, Image, KeepTogether,
                                    PageTemplate, Paragraph, Spacer, Table, TableStyle)
    from reportlab.lib import colors

    fdir = "/System/Library/Fonts/Supplemental/"
    try:
        for name, fn in (("TNR", "Times New Roman.ttf"), ("TNR-B", "Times New Roman Bold.ttf"),
                         ("TNR-I", "Times New Roman Italic.ttf"), ("TNR-BI", "Times New Roman Bold Italic.ttf"),
                         ("CNR", "Courier New.ttf")):
            pdfmetrics.registerFont(TTFont(name, os.path.join(fdir, fn)))
        pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
        SERIF, MONO = "TNR", "CNR"
    except Exception:                      # non-macOS: built-in Type-1 fonts (no Greek glyphs)
        SERIF, MONO = "Times-Roman", "Courier"

    order = cite_order(doc)
    num = {k: i + 1 for i, k in enumerate(order)}

    def rl(s):
        out = []
        for tok in TOKEN.split(s):
            if not tok:
                continue
            if tok == "<tt>":
                out.append(f'<font face="{MONO}" size="8.6">')
            elif tok == "</tt>":
                out.append("</font>")
            elif tok == "<sub>":
                out.append('<sub>')
            elif tok == "<super>":
                out.append('<super rise="3" size="7">')
            elif tok in ("</sub>", "</super>"):
                out.append(tok)
            elif tok in ("<i>", "</i>", "<b>", "</b>"):
                out.append(tok)
            elif tok.startswith("{c:"):
                ns = sorted(num[k.strip()] for k in tok[3:-1].split(","))
                out.append("[" + "], [".join(str(n) for n in ns) + "]")
            else:
                out.append(tok.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        return "".join(out)

    PW, PH = letter
    LM, RM, TM, BM = 0.625 * inch, 0.625 * inch, 0.75 * inch, 1.0 * inch
    GAP = 0.25 * inch
    CW = (PW - LM - RM - GAP) / 2
    body = ParagraphStyle("body", fontName=SERIF, fontSize=10, leading=12.2, alignment=TA_JUSTIFY,
                          firstLineIndent=10, spaceAfter=0)
    st = {
        "title": ParagraphStyle("t", fontName=SERIF, fontSize=22, leading=26, alignment=TA_CENTER, spaceAfter=10),
        "auth": ParagraphStyle("a", fontName=SERIF, fontSize=10, leading=12, alignment=TA_CENTER),
        "abs": ParagraphStyle("ab", fontName="TNR-B" if SERIF == "TNR" else "Times-Bold", fontSize=9,
                              leading=10.6, alignment=TA_JUSTIFY, firstLineIndent=10),
        "h1": ParagraphStyle("h1", fontName=SERIF, fontSize=10, leading=12, alignment=TA_CENTER,
                             spaceBefore=8, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName="TNR-I" if SERIF == "TNR" else "Times-Italic", fontSize=10,
                             leading=12, spaceBefore=5, spaceAfter=2),
        "cap": ParagraphStyle("cap", fontName=SERIF, fontSize=8, leading=9.4, alignment=TA_JUSTIFY),
        "tcap": ParagraphStyle("tc", fontName=SERIF, fontSize=8, leading=9.4, alignment=TA_CENTER),
        "cell": ParagraphStyle("cell", fontName=SERIF, fontSize=8, leading=9.2, alignment=TA_LEFT),
        "bul": ParagraphStyle("bul", parent=body, firstLineIndent=0, leftIndent=12, bulletIndent=3, spaceAfter=1),
        "ref": ParagraphStyle("ref", fontName=SERIF, fontSize=8, leading=9.4, alignment=TA_LEFT,
                              leftIndent=16, firstLineIndent=-16, spaceAfter=1.5),
        "code": ParagraphStyle("code", fontName=MONO, fontSize=7, leading=8.6, leftIndent=4),
        "alg": ParagraphStyle("alg", fontName=SERIF, fontSize=8.4, leading=10.2),
        "eq": ParagraphStyle("eq", fontName=SERIF, fontSize=10, leading=13, alignment=TA_CENTER),
    }

    def roman(n):
        return ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][n - 1]

    def smallcaps(t):
        return "".join(f'<font size="10">{w[0]}</font><font size="8">{w[1:].upper()}</font>' if w else ""
                       for w in t.split(" ")).replace("</font><font", "</font> <font") \
            if False else " ".join(f'{w[:1].upper()}<font size="7.6">{w[1:].upper()}</font>' for w in t.split(" "))

    def img(name, width):
        r = ImageReader(os.path.join(FIG, name + ".png"))
        w, h = r.getSize()
        return Image(os.path.join(FIG, name + ".png"), width=width, height=width * h / w)

    story = []
    # ---- page-1 header (full-width frame)
    story.append(Paragraph(rl(doc["title"]), st["title"]))
    story.append(Paragraph(f"<b>{rl(author['name'])}</b><br/><i>{rl(author['department'])}</i><br/>"
                           f"<i>{rl(author['institution'])}</i><br/>{rl(author['location'])}<br/>"
                           f"Student ID: {rl(author['student_id'])} &nbsp;&nbsp; {rl(author['email'])}",
                           st["auth"]))
    story.append(FrameBreak())
    story.append(Paragraph("<b><i>Abstract</i></b>—" + rl(doc["abstract"]), st["abs"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b><i>Index Terms</i></b>—" + rl(doc["keywords"]), st["abs"]))

    sec = sub = 0
    fig_no = 1          # Fig. 1 = architecture (drawn on page 2)
    tab_no = 0
    first_par = False
    for b in doc["body"]:
        kind = b[0]
        if kind == "h1":
            sec += 1; sub = 0
            story.append(Paragraph(f"{roman(sec)}. {smallcaps(rl(b[1]))}", st["h1"]))
            first_par = True
        elif kind == "h2":
            sub += 1
            story.append(Paragraph(f"{chr(64 + sub)}. {rl(b[1])}", st["h2"]))
            first_par = True
        elif kind == "p":
            stl = ParagraphStyle("p0", parent=body, firstLineIndent=0 if first_par and False else 10)
            story.append(Paragraph(rl(b[1]), stl))
            first_par = False
        elif kind == "bullets":
            for x in b[1]:
                story.append(Paragraph(rl(x), st["bul"], bulletText="•"))
        elif kind == "eq":
            t = Table([[Paragraph("<br/>".join(rl(x) for x in b[2].split("<br/>")), st["eq"]),
                        Paragraph(f"({b[3]})", st["eq"])]],
                      colWidths=[CW - 24, 24])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 3),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            story.append(t)
        elif kind == "fig":
            fig_no += 1
            story.append(KeepTogether([Spacer(1, 4), img(b[1], CW), Spacer(1, 3),
                                       Paragraph(f"Fig. {fig_no}. " + rl(b[2]), st["cap"]), Spacer(1, 6)]))
        elif kind == "table":
            tab_no += 1
            _, cap, head, rows, widths = b
            data = [[Paragraph(f"<b>{rl(h)}</b>", st["cell"]) for h in head]] + \
                   [[Paragraph(rl(c), st["cell"]) for c in r] for r in rows]
            t = Table(data, colWidths=[w * CW for w in widths])
            t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
                                   ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                                   ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                   ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
            story.append(KeepTogether([Spacer(1, 4),
                                       Paragraph(f"TABLE {roman(tab_no)}<br/>{smallcaps(rl(cap))}", st["tcap"]),
                                       Spacer(1, 3), t, Spacer(1, 6)]))
        elif kind == "alg":
            _, title, lines = b
            rows = [[Paragraph(f"<b>{rl(title)}</b>", st["alg"])]] + \
                   [[Paragraph(f'<font size="6.5">{i}:</font>&nbsp;' + "&nbsp;" * (2 + 5 * ind) + rl(t), st["alg"])]
                    for i, (ind, t) in enumerate(lines, 1)]
            t = Table(rows, colWidths=[CW - 4])
            t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                                   ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.black),
                                   ("TOPPADDING", (0, 0), (-1, -1), 0.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.6),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
            story.append(KeepTogether([Spacer(1, 4), t, Spacer(1, 6)]))

    story.append(Paragraph(smallcaps("Acknowledgment"), st["h1"]))
    story.append(Paragraph("Prepared for " + rl(author["course"]) + ". Evaluation results use simulated "
                           "personas only; no human-subject data were collected.", body))
    story.append(Paragraph(smallcaps("References"), st["h1"]))
    refs = dict(doc["references"])
    for k in order:
        story.append(Paragraph(f"[{num[k]}]&nbsp;&nbsp;" + rl(refs[k]), st["ref"]))
    story.append(Paragraph("A" + "PPENDIX", st["h1"]))
    story.append(Paragraph("<i>Code Repository and Reproduction</i>", st["h2"]))
    for kind, val in doc["appendix"]:
        if kind == "p":
            story.append(Paragraph(rl(val), ParagraphStyle("ap", parent=body, firstLineIndent=0, spaceAfter=3,
                                                           alignment=TA_LEFT)))
        else:
            story.append(Spacer(1, 2))
            for line in val:
                story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                       .replace(" ", "&nbsp;"), st["code"]))
            story.append(Spacer(1, 4))

    # ---- page templates
    head_h = 2.2 * inch
    arch = ImageReader(os.path.join(FIG, "fig_architecture.png"))
    aw, ah = arch.getSize()
    arch_w = PW - LM - RM
    arch_h = arch_w * ah / aw
    arch_cap = Paragraph("Fig. 1. CogniFin Coach architecture. Perception turns quiz answers and decisions "
                         "into trait priors, events and opportunity contexts; the dual-layer user model, "
                         "mismatch detector and knowledge base perform inference; the coach generates a "
                         "validated message while “Why this?” is assembled deterministically; the user’s "
                         "next decision closes the loop.", st["cap"])
    cap_w, cap_h = arch_cap.wrap(arch_w, 100)
    arch_block = arch_h + cap_h + 14

    def cols(top_offset):
        h = PH - TM - BM - top_offset
        return [Frame(LM, BM, CW, h, id="c1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
                Frame(LM + CW + GAP, BM, CW, h, id="c2", leftPadding=0, rightPadding=0, topPadding=0,
                      bottomPadding=0)]

    def footer(c, d):
        c.setFont(SERIF, 8)
        c.drawCentredString(PW / 2, 0.55 * inch, str(d.page))

    def draw_arch(c, d):
        footer(c, d)
        y_top = PH - TM
        c.drawImage(arch, LM, y_top - arch_h, width=arch_w, height=arch_h)
        arch_cap.drawOn(c, LM, y_top - arch_h - 4 - cap_h)

    first = PageTemplate(id="first", onPage=footer,
                         frames=[Frame(LM, PH - TM - head_h, PW - LM - RM, head_h, id="head",
                                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
                         + cols(head_h + 8))
    archp = PageTemplate(id="arch", onPage=draw_arch, frames=cols(arch_block))
    normal = PageTemplate(id="normal", onPage=footer, frames=cols(0))
    class Doc(BaseDocTemplate):
        def afterPage(self):                 # page 1 -> architecture page -> normal pages
            self.handle_nextPageTemplate("arch" if self.page == 1 else "normal")

    d = Doc(path, pagesize=letter, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                        title="CogniFin Coach", author=author["name"],
                        subject="CPE 663 Cognitive Computing term project paper")
    d.addPageTemplates([first, archp, normal])
    d.build(story)
    return d.page


def main():
    with open(os.path.join(HERE, "author.json")) as f:
        author = json.load(f)
    author["repo_url"] = author["repo_url"].strip().removesuffix(".git")   # display form
    doc = content.build(author)
    words = len(re.sub(r"<[^>]+>|\{c:[^}]+\}", "", doc["abstract"]).split())
    build_tex(doc, author, os.path.join(HERE, "CogniFin_Coach_IEEE.tex"))
    pages = build_pdf(doc, author, os.path.join(HERE, "CogniFin_Coach_IEEE.pdf"))
    print(f"abstract words: {words}; PDF pages: {pages}")


if __name__ == "__main__":
    main()
