"""Beregning av linjesummer og MVA, og norsk tallformat."""

MVA_SATS = 0.25


def kr(beløp: float) -> str:
    """12345.5 -> '12 345,50 kr'"""
    s = f"{beløp:,.2f}".replace(",", " ").replace(".", ",")
    return f"{s} kr"


def beregn(linjer: list[dict], mva: bool = True) -> dict:
    rensede = []
    for l in linjer:
        beskrivelse = str(l.get("Beskrivelse") or "").strip()
        if not beskrivelse:
            continue
        antall = float(l.get("Antall") or 0)
        pris = float(l.get("Pris eks. mva") or 0)
        rensede.append({
            "Beskrivelse": beskrivelse,
            "Antall": antall,
            "Enhet": str(l.get("Enhet") or "stk"),
            "Pris eks. mva": pris,
            "Sum": round(antall * pris, 2),
        })
    netto = round(sum(l["Sum"] for l in rensede), 2)
    mva_beløp = round(netto * MVA_SATS, 2) if mva else 0.0
    return {
        "linjer": rensede,
        "netto": netto,
        "mva": mva_beløp,
        "total": round(netto + mva_beløp, 2),
    }
