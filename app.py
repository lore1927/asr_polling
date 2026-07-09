import streamlit as st
from queue_it_automation import QueueItAutomation

st.set_page_config(page_title="Queue Automation", layout="centered")

st.title("Automazione Queue-it AS Roma")
st.write("Verifica o modifica l'URL target e avvia lo script.")

# URL di default impostato nella casella di testo
url_default = "https://biglietti.asroma.com/tickets/season/pre/MAN132/D19"

# Casella di testo modificabile
url_input = st.text_input("URL Target: ", value=url_default)

# Pulsante di avvio
if st.button("Avvia"):
    with st.spinner("In corso... Riavvia la pagina per annullare coglione"):
        
        # Inizializzazione dello script con l'URL della casella di testo
        automation = QueueItAutomation(
            vendor="webroma", 
            language="IT", 
            target_url=url_input,
            event_id="asrabbonamenti2022"
        )
        
        success, redirect_url = automation.run(max_polling_attempts=450)
        
        if success:
            st.success("Finocchiò (Lorenzo no) procedura completata sbrigateeeeeeee")
            # Mostra l'URL ottenuto in una casella di testo sotto il pulsante
            st.text_input("URL di accesso: ", value=redirect_url)
        else:
            st.error("Procedura fallita o timeout")