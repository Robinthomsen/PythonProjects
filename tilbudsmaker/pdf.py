"""Lager et pent tilbud som PDF."""

from datetime import date

from fpdf import FPDF

from beregning import kr
from db import LOGO_PATH

AKSENT = (31, 78, 121)
GRÅ = (110, 110, 110)
LYS = (238, 242, 246)


def _fmt_antall(x: float) -> str:
    return str(int(x)) if x == int(x) else f"{x:.2f}".replace(".", ",")


def _fmt_dato(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%d.%m.%Y")


def lag_pdf(firma: dict, tilbud: dict) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    W = pdf.w - 36

    # Topp: logo + firmainfo
    y0 = 18
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=18, y=y0, h=18)
    pdf.set_xy(18, y0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRÅ)
    info = [firma.get("navn", ""), firma.get("adresse", ""), firma.get("postnr_sted", "")]
    if firma.get("orgnr"):
        info.append(f"Org.nr. {firma['orgnr']} MVA")
    if firma.get("telefon"):
        info.append(f"Tlf. {firma['telefon']}")
    if firma.get("epost"):
        info.append(firma["epost"])
    for linje in [i for i in info if i]:
        pdf.set_x(18)
        pdf.cell(W, 4.5, linje, align="R", new_x="LMARGIN", new_y="NEXT")

    # Tittel
    pdf.ln(8)
    pdf.set_text_color(*AKSENT)
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(W, 12, "TILBUD", new_x="LMARGIN", new_y="NEXT")

    # Kunde + metadata
    pdf.ln(2)
    y = pdf.get_y()
    k = tilbud["kunde"]
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(W / 2, 5, "Til:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for linje in [k.get("navn"), k.get("adresse"), k.get("postnr_sted"), k.get("epost")]:
        if linje:
            pdf.cell(W / 2, 5, linje, new_x="LMARGIN", new_y="NEXT")
    y_slutt = pdf.get_y()

    meta = [
        ("Tilbudsnr.", str(tilbud["nummer"])),
        ("Dato", _fmt_dato(tilbud["dato"])),
        ("Gyldig til", _fmt_dato(tilbud["gyldig_til"])),
    ]
    pdf.set_y(y)
    for etikett, verdi in meta:
        pdf.set_x(18 + W / 2)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRÅ)
        pdf.cell(W / 4, 5, etikett, align="R")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(W / 4, 5, verdi, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(max(y_slutt, pdf.get_y()) + 4)

    if tilbud.get("prosjekt"):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(W, 6, tilbud["prosjekt"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Linjetabell
    kol = [W * 0.46, W * 0.11, W * 0.09, W * 0.16, W * 0.18]
    hode = ["Beskrivelse", "Antall", "Enhet", "Pris", "Sum"]
    pdf.set_fill_color(*AKSENT)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for i, (b, t) in enumerate(zip(kol, hode)):
        pdf.cell(b, 7, t, fill=True, align="L" if i == 0 else "R")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for n, l in enumerate(tilbud["linjer"]):
        pdf.set_fill_color(*(LYS if n % 2 else (255, 255, 255)))
        verdier = [
            l["Beskrivelse"], _fmt_antall(l["Antall"]), l["Enhet"],
            kr(l["Pris eks. mva"]), kr(l["Sum"]),
        ]
        for i, (b, v) in enumerate(zip(kol, verdier)):
            pdf.cell(b, 7, v, fill=True, align="L" if i == 0 else "R")
        pdf.ln()

    # Summer
    pdf.ln(3)
    summer = [("Sum eks. mva", tilbud["netto"])]
    if tilbud["mva"]:
        summer.append(("MVA 25 %", tilbud["mva"]))
    pdf.set_font("Helvetica", "", 10)
    for etikett, v in summer:
        pdf.set_x(18 + W * 0.55)
        pdf.cell(W * 0.25, 6, etikett, align="R")
        pdf.cell(W * 0.20, 6, kr(v), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18 + W * 0.55)
    pdf.set_draw_color(*AKSENT)
    pdf.line(18 + W * 0.55, pdf.get_y() + 1, 18 + W, pdf.get_y() + 1)
    pdf.ln(2)
    pdf.set_x(18 + W * 0.55)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*AKSENT)
    pdf.cell(W * 0.25, 8, "Totalt", align="R")
    pdf.cell(W * 0.20, 8, kr(tilbud["total"]), align="R", new_x="LMARGIN", new_y="NEXT")

    # Betingelser / notat
    pdf.set_text_color(0, 0, 0)
    for tittel, tekst in [("Merknader", tilbud.get("notat")), ("Betingelser", tilbud.get("betingelser"))]:
        if tekst:
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(W, 5, tittel, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(W, 4.5, tekst)

    # Bunntekst
    if firma.get("kontonr"):
        pdf.set_y(-22)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRÅ)
        pdf.cell(W, 4, f"Kontonr. {firma['kontonr']}  ·  {firma.get('navn', '')}", align="C")

    return bytes(pdf.output())
