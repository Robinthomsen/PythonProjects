"""Tilbudsmaker – profesjonelle tilbud for håndverkere på under ett minutt."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db
from beregning import beregn, kr
from pdf import lag_pdf

GRATIS_GRENSE = 3  # tilbud per måned i gratisversjonen
ENHETER = ["stk", "timer", "m", "m²", "m³", "kg", "pakke", "dag"]

st.set_page_config(page_title="Tilbudsmaker", page_icon="🧾", layout="wide")

firma = db.get_company()

with st.sidebar:
    st.title("🧾 Tilbudsmaker")
    side = st.radio("Meny", ["Nytt tilbud", "Tidligere tilbud", "Firmaprofil"], label_visibility="collapsed")
    st.divider()
    if firma["pro"]:
        st.success("Pro-konto ✨")
    else:
        brukt = db.quotes_this_month()
        st.caption(f"Gratisversjon: {brukt} av {GRATIS_GRENSE} tilbud brukt denne måneden")
        st.progress(min(brukt / GRATIS_GRENSE, 1.0))
        st.caption("**Pro – 149 kr/mnd:** ubegrenset tilbud, egen logo, e-post til kunde.")


# ---------------------------------------------------------------- Firmaprofil
if side == "Firmaprofil":
    st.header("Firmaprofil")
    st.caption("Dette vises på alle tilbudene dine.")
    with st.form("firma"):
        c1, c2 = st.columns(2)
        ny = dict(firma)
        ny["navn"] = c1.text_input("Firmanavn", firma["navn"])
        ny["orgnr"] = c2.text_input("Org.nr.", firma["orgnr"])
        ny["adresse"] = c1.text_input("Adresse", firma["adresse"])
        ny["postnr_sted"] = c2.text_input("Postnr. og sted", firma["postnr_sted"])
        ny["telefon"] = c1.text_input("Telefon", firma["telefon"])
        ny["epost"] = c2.text_input("E-post", firma["epost"])
        ny["kontonr"] = c1.text_input("Kontonummer", firma["kontonr"])
        logo = c2.file_uploader("Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
        ny["standard_betingelser"] = st.text_area(
            "Standard betingelser",
            firma["standard_betingelser"]
            or "Tilbudet er gyldig i 30 dager. Betaling 14 dager netto. "
               "Endringer og tilleggsarbeid faktureres etter medgått tid.",
        )
        if st.form_submit_button("Lagre", type="primary"):
            db.save_company(ny)
            if logo:
                db.LOGO_PATH.write_bytes(logo.getvalue())
            st.success("Lagret!")
            st.rerun()
    if db.LOGO_PATH.exists():
        st.image(str(db.LOGO_PATH), width=160, caption="Nåværende logo")


# ---------------------------------------------------------------- Nytt tilbud
elif side == "Nytt tilbud":
    st.header("Nytt tilbud")
    if not firma["navn"]:
        st.info("👋 Start med å fylle ut **Firmaprofil** i menyen, så ser tilbudene dine proffe ut.")

    sperret = not firma["pro"] and db.quotes_this_month() >= GRATIS_GRENSE
    if sperret:
        st.warning(f"Du har brukt alle {GRATIS_GRENSE} gratis tilbud denne måneden. Oppgrader til Pro for ubegrenset bruk.")

    st.subheader("Kunde")
    c1, c2 = st.columns(2)
    kunde = {
        "navn": c1.text_input("Kundens navn *"),
        "epost": c2.text_input("Kundens e-post"),
        "adresse": c1.text_input("Adresse"),
        "postnr_sted": c2.text_input("Postnr. og sted"),
    }
    c1, c2, c3 = st.columns([2, 1, 1])
    prosjekt = c1.text_input("Prosjekt / overskrift", placeholder="F.eks. Oppussing av bad")
    dato = c2.date_input("Dato", date.today(), format="DD.MM.YYYY")
    gyldig = c3.date_input("Gyldig til", date.today() + timedelta(days=30), format="DD.MM.YYYY")

    st.subheader("Linjer")
    if "linjer" not in st.session_state:
        st.session_state.linjer = pd.DataFrame(
            [{"Beskrivelse": "", "Antall": 1.0, "Enhet": "timer", "Pris eks. mva": 0.0}]
        )
    redigert = st.data_editor(
        st.session_state.linjer,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "Beskrivelse": st.column_config.TextColumn(width="large"),
            "Antall": st.column_config.NumberColumn(min_value=0, step=0.5),
            "Enhet": st.column_config.SelectboxColumn(options=ENHETER),
            "Pris eks. mva": st.column_config.NumberColumn(min_value=0, step=50, format="%.2f kr"),
        },
        key="linje_editor",
    )
    med_mva = st.toggle("Legg til 25 % MVA", value=True)
    res = beregn(redigert.to_dict("records"), mva=med_mva)

    m1, m2, m3 = st.columns(3)
    m1.metric("Sum eks. mva", kr(res["netto"]))
    m2.metric("MVA", kr(res["mva"]))
    m3.metric("Totalt", kr(res["total"]))

    notat = st.text_area("Merknader til kunden (valgfritt)")
    betingelser = st.text_area("Betingelser", firma["standard_betingelser"])

    if st.button("Lag tilbud (PDF)", type="primary", disabled=sperret):
        if not kunde["navn"]:
            st.error("Fyll inn kundens navn.")
        elif not res["linjer"]:
            st.error("Legg til minst én linje med beskrivelse.")
        else:
            tilbud = {
                "nummer": db.next_quote_number(),
                "dato": dato.isoformat(),
                "gyldig_til": gyldig.isoformat(),
                "kunde": kunde,
                "prosjekt": prosjekt,
                "notat": notat,
                "betingelser": betingelser,
                **res,
            }
            db.save_quote(tilbud)
            st.session_state.siste_pdf = (tilbud["nummer"], lag_pdf(firma, tilbud))
            st.session_state.pop("linjer", None)
            st.success(f"Tilbud {tilbud['nummer']} er laget!")

    if "siste_pdf" in st.session_state:
        nr, data = st.session_state.siste_pdf
        st.download_button(
            f"⬇️ Last ned tilbud {nr}", data, file_name=f"tilbud-{nr}.pdf", mime="application/pdf"
        )


# ---------------------------------------------------------------- Historikk
else:
    st.header("Tidligere tilbud")
    tilbud_liste = db.list_quotes()
    if not tilbud_liste:
        st.info("Ingen tilbud ennå.")
    for t in tilbud_liste:
        with st.expander(f"#{t['nummer']} · {t['kunde']['navn']} · {t.get('prosjekt') or ''} · {kr(t['total'])}"):
            st.dataframe(pd.DataFrame(t["linjer"]), hide_index=True, width="stretch")
            st.download_button(
                "Last ned PDF", lag_pdf(firma, t),
                file_name=f"tilbud-{t['nummer']}.pdf", mime="application/pdf", key=f"dl{t['nummer']}",
            )
