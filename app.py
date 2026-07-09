import streamlit as st
import time
import json
from datetime import datetime
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
    # Area dedicata ai log dinamici che si aggiorneranno a schermo
    log_area = st.empty()
    
    with st.spinner("In corso... Riavvia la pagina per annullare coglione"):
        
        # 1. Inizializzazione dello script
        automation = QueueItAutomation(
            vendor="webroma", 
            language="IT", 
            target_url=url_input,
            event_id="asrabbonamenti2022"
        )
        
        # 2. Richiesta iniziale di ingresso in coda (Enqueue)
        enqueue_url = f"{automation.BASE_URL}/spa-api/queue/{automation.CUSTOMER_ID}/{automation.EVENT_ID}/enqueue"
        enqueue_params = {"cid": "it-IT", "l": "Asroma prod Abbonamenti", "t": automation.target_url}
        
        log_area.code(
            f"[{datetime.now().strftime('%H:%M:%S')}] RICHIESTA ENQUEUE\n"
            f"URL: {enqueue_url}\n"
            f"Params: {json.dumps(enqueue_params, indent=2)}\n"
            f"Inviando richiesta..."
        )
        
        if not automation.step_enqueue():
            st.error("Procedura fallita durante l'enqueue.")
            st.stop()
            
        automation.step_generate_session_params()
        
        # 3. Polling visibile a schermo (Max 15 minuti = 450 tentativi da 2 secondi)
        success = False
        max_attempts = 450
        poll_interval = 2
        
        for attempt in range(1, max_attempts + 1):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            try:
                # Costruisce la chiamata di status
                url = f"{automation.BASE_URL}/spa-api/queue/{automation.CUSTOMER_ID}/{automation.EVENT_ID}/{automation.queue_id}/status"
                params = {
                    "cid": "it-IT", "l": "Asroma prod Abbonamenti",
                    "t": automation.target_url, "seid": automation.seid, "sets": automation.sets
                }
                body = {
                    "targetUrl": automation.target_url, "customUrlParams": "", "layoutVersion": 180105136056,
                    "layoutName": "Asroma prod Abbonamenti", "isClientRedayToRedirect": False, "isBeforeOrIdle": False
                }
                
                # Esegue la chiamata
                response = automation.session.post(url, params=params, json=body, timeout=10)
                status_code = response.status_code
                data = response.json()
                
                # Filtra e tiene solo le informazioni pulite della risposta
                clean_response = {
                    "queueId": automation.queue_id,
                    "isBeforeOrIdle": data.get("isBeforeOrIdle"),
                    "QueueState": data.get("QueueState"),
                    "forecastStatus": data.get("forecastStatus"),
                    "ticket": data.get("ticket", {})
                }
                
                # Aggiorna il log a schermo con input ed esito pulito
                log_area.code(
                    f"[{timestamp}] TENTATIVO {attempt}/{max_attempts}\n"
                    f"--------------------------------------------------\n"
                    f"HTTP Status: {status_code}\n"
                    f"URL Status: {url}\n"
                    f"Params: {json.dumps(params, indent=2)}\n"
                    f"Body: {json.dumps(body, indent=2)}\n"
                    f"--------------------------------------------------\n"
                    f"Risposta Server Filtrata:\n{json.dumps(clean_response, indent=2)}"
                )
                
                # Controllo se il turno è arrivato
                if "redirectUrl" in data and data.get("isRedirectToTarget"):
                    automation.redirect_url = data["redirectUrl"]
                    success = True
                    break
                    
            except Exception as e:
                log_area.code(f"[{timestamp}] Errore connessione al tentativo {attempt}: {str(e)}")
            
            time.sleep(poll_interval)
        
        # 4. Esito finale
        if success:
            log_area.empty() # Pulisce la zona log per fare spazio al risultato
            st.success("Finocchiò (Lorenzo no) procedura completata sbrigateeeeeeee")
            st.text_input("URL di accesso: ", value=automation.redirect_url)
        else:
            log_area.code(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout raggiunto.")
            st.error("Procedura fallita o timeout")
