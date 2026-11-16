import streamlit as st

st.title("Min første nettside i Python")
st.write(
    "Dette nettstedet kjører lokalt på maskinen min, skrevet i Neovim og drevet av Python!"
)

# Et enkelt interaktivt felt
navn = st.text_input("Hva heter du?")
if navn:
    st.success(f"Hei, {navn}! Velkommen til din egen web-app.")

# En knapp som gjør noe gøy
if st.button("Trykk her for feiring"):
    st.balloons()
    st.write("Gratulerer! Du har nettopp laget en dynamisk nettside.")
