import streamlit as st
import time
from datetime import datetime
from queue_it_automation import QueueItAutomation

st.set_page_config(page_title="Queue Automation", layout="centered")

st.title("Automazione Queue-it AS Roma")
st.write("Verifica o modifica i parametri e avvia lo script.")


# ============================================================
# PARAMETRI PRINCIPALI
# ============================================================

url_default = "https://biglietti.asroma.com/tickets/pre/MAN133/001"

url_input = st.text_input(
    "URL Target:",
    value=url_default
)

event_id_input = st.text_input(
    "Event ID:",
    value="asrbiglietti2021drb"
)

layout_version_input = st.number_input(
    "Layout Version:",
    value=180627395026,
    step=1,
    format="%d"
)

# Nome del layout utilizzato nel BODY
layout_name_input = st.text_input(
    "Layout Name:",
    value="Asroma prod finale"
)

# Valore del parametro "l" utilizzato nella query string.
# Viene lasciato separato perché può essere diverso
# dal Layout Name del body.
layout_name_query_input = st.text_input(
    "Layout Name Query (parametro l):",
    value="Asroma+prod+finale"
)


# ============================================================
# PARAMETRI EXTRA DELL'URL
# ============================================================

use_extra_url_params = st.checkbox(
    "Abilita parametri extra URL"
)

extra_url_params_input = st.text_input(
    "Parametri extra URL:",
    value="",
    placeholder="?promo=VENPRE&vendor=venpre",
    disabled=not use_extra_url_params
)

st.caption(
    "Puoi inserirli con o senza '?'. "
    "Esempio: ?promo=VENPRE&vendor=venpre"
)


# ============================================================
# AVVIO
# ============================================================

if st.button("Avvia"):

    with st.spinner("In corso... Riavvia la pagina per annullare"):

        # ----------------------------------------------------
        # Inizializzazione dello script
        # ----------------------------------------------------

        automation = QueueItAutomation(
            language="it",
            target_url=url_input,
            event_id=event_id_input,
            layout_version=layout_version_input,
            layout_name=layout_name_input,
            layout_name_query=layout_name_query_input,
            extra_url_params=extra_url_params_input,
            use_extra_url_params=use_extra_url_params
        )

        log_area = st.empty()

        # ----------------------------------------------------
        # Richiesta iniziale di ingresso in coda (Enqueue)
        # ----------------------------------------------------

        log_area.code(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Richiesta Enqueue in corso con "
            f"Event ID '{automation.EVENT_ID}' "
            f"e LayoutVersion {automation.layout_version}..."
        )

        success_enqueue, msg_enqueue = automation.step_enqueue()

        if not success_enqueue:
            st.error(
                f"Procedura fallita durante l'enqueue: "
                f"{msg_enqueue}"
            )
            st.stop()

        automation.step_generate_session_params()

        # ----------------------------------------------------
        # Polling
        # Max 15 minuti = 450 tentativi da 2 secondi
        # ----------------------------------------------------

        success = False
        max_attempts = 450
        poll_interval = 2

        for attempt in range(1, max_attempts + 1):

            timestamp = datetime.now().strftime("%H:%M:%S")

            try:

                # Costruisce la chiamata di status
                url = (
                    f"{automation.BASE_URL}/spa-api/queue/"
                    f"{automation.CUSTOMER_ID}/"
                    f"{automation.EVENT_ID}/"
                    f"{automation.queue_id}/status"
                )

                params = {
                    "cid": "it-IT",
                    "l": automation.layout_name_query,
                    "t": automation.target_url,
                    "seid": automation.seid,
                    "sets": automation.sets
                }

                body = {
                    "targetUrl": automation.target_url,
                    "customUrlParams": "",
                    "layoutVersion": automation.layout_version,
                    "layoutName": automation.layout_name,
                    "isClientRedayToRedirect": True,
                    "isBeforeOrIdle": False
                }

                # ------------------------------------------------
                # Esegue la chiamata
                # ------------------------------------------------

                response = automation.session.post(
                    url,
                    params=params,
                    json=body,
                    timeout=10
                )

                status_code = response.status_code
                data = response.json()

                # ------------------------------------------------
                # Estrae i dati utili
                # ------------------------------------------------

                ticket = data.get("ticket", {})

                inline_ahead = ticket.get(
                    "usersInLineAheadOfYou",
                    "0"
                )

                wait_time = ticket.get(
                    "whichIsIn",
                    "N/D"
                )

                forecast = data.get(
                    "forecastStatus",
                    "N/D"
                )

                # ------------------------------------------------
                # Log
                # ------------------------------------------------

                input_str = (
                    f"event:{automation.EVENT_ID} | "
                    f"layoutVer:{automation.layout_version} | "
                    f"layoutName:{automation.layout_name} | "
                    f"l:{automation.layout_name_query} | "
                    f"target:{automation.target_url} | "
                    f"seid:{automation.seid[:8]}..."
                )

                log_area.code(
                    f"[{timestamp}] "
                    f"TENTATIVO {attempt}/{max_attempts} | "
                    f"Queue ID: {automation.queue_id}\n"
                    f"INPUT  -> HTTP POST | {url}\n"
                    f"PARAMS/BODY -> {input_str}\n"
                    f"OUTPUT -> HTTP {status_code} | "
                    f"Stato: {forecast} | "
                    f"In coda davanti: {inline_ahead} | "
                    f"Attesa: {wait_time}"
                )

                # ------------------------------------------------
                # Controllo se il turno è arrivato
                # ------------------------------------------------

                if (
                    "redirectUrl" in data
                    and data.get("isRedirectToTarget")
                ):
                    automation.redirect_url = data["redirectUrl"]
                    success = True
                    break

            except Exception as e:

                log_area.code(
                    f"[{timestamp}] "
                    f"Errore connessione al tentativo "
                    f"{attempt}: {str(e)}"
                )

            time.sleep(poll_interval)

        # ----------------------------------------------------
        # Esito finale
        # ----------------------------------------------------

        if success:

            log_area.empty()

            st.success("Procedura completata!")

            st.write("URL di accesso:")

            st.code(
                automation.redirect_url,
                language="text"
            )

            st.link_button(
                "Apri link di accesso",
                automation.redirect_url
            )

        else:

            log_area.code(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"Timeout raggiunto."
            )

            st.error(
                "Procedura fallita o timeout"
            )
