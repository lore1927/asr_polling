#!/usr/bin/env python3

import requests
import uuid
import time
from typing import Optional, Tuple


class QueueItAutomation:
    """Automazione del flusso Queue-it per AS Roma"""

    BASE_URL = "https://bestunion.queue-it.net"
    CUSTOMER_ID = "bestunion"

    def __init__(
        self,
        language: str = "it",
        target_url: str = None,
        event_id: str = "asrbiglietti2021drb",
        layout_version: int = 180627395026,
        layout_name: str = "Asroma prod finale",
        layout_name_query: str = "Asroma+prod+finale",
        extra_url_params: str = "",
        use_extra_url_params: bool = False
    ):

        self.language = language
        self.session = requests.Session()

        # ========================================================
        # HEADER
        # ========================================================

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/152.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "application/json, text/javascript, */*; q=0.01"
            ),
            "Accept-Language": (
                "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
            ),
            "Content-Type": "application/json",
            "Origin": self.BASE_URL,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "X-Queueit-QPage-Referral": "https://www.asroma.com/"
        })

        # ========================================================
        # PARAMETRI QUEUE-IT
        # ========================================================

        self.EVENT_ID = event_id

        self.layout_version = int(layout_version)

        # Versione con gli spazi.
        # Utilizzata nel campo "layoutName" del body.
        self.layout_name = layout_name

        # Versione con i "+".
        # Utilizzata nel parametro "l" della query string.
        self.layout_name_query = layout_name_query

        # ========================================================
        # COSTRUZIONE TARGET URL
        # ========================================================

        base_target = (
            target_url.split("?")[0]
            if target_url
            else (
                "https://biglietti.asroma.com/"
                "tickets/pre/MAN133/001"
            )
        )

        self.target_url = base_target

        # --------------------------------------------------------
        # Parametri extra
        # --------------------------------------------------------
        #
        # Esempi accettati:
        #
        # ?promo=VENPRE&vendor=venpre
        #
        # oppure:
        #
        # promo=VENPRE&vendor=venpre
        #
        # Il "?" viene aggiunto automaticamente.
        # --------------------------------------------------------

        if use_extra_url_params and extra_url_params:

            extra = extra_url_params.strip()

            if extra.startswith("?"):
                extra = extra[1:]

            if extra:
                self.target_url += "?" + extra

        # ========================================================
        # VARIABILI DELLA CODA
        # ========================================================

        self.queue_id: Optional[str] = None
        self.seid: Optional[str] = None
        self.sets: Optional[int] = None
        self.redirect_url: Optional[str] = None

    # ============================================================
    # ENQUEUE
    # ============================================================

    def step_enqueue(self) -> Tuple[bool, str]:

        url = (
            f"{self.BASE_URL}/spa-api/queue/"
            f"{self.CUSTOMER_ID}/"
            f"{self.EVENT_ID}/enqueue"
        )

        # --------------------------------------------------------
        # Referrer dinamico basato sull'URL della coda Queue-it
        # --------------------------------------------------------

        queue_page_url = (
            f"{self.BASE_URL}/"
            f"?c={self.CUSTOMER_ID}"
            f"&e={self.EVENT_ID}"
            f"&cid={self.language.lower()}-"
            f"{self.language.upper()}"
            f"&t={self.target_url}"
        )

        headers = {
            "Referer": queue_page_url
        }

        # --------------------------------------------------------
        # Query parameters
        # --------------------------------------------------------

        params = {
            "cid": "it-IT",
            "l": self.layout_name_query,
            "t": self.target_url
        }

        # --------------------------------------------------------
        # Body
        # --------------------------------------------------------

        body = {
            "challengeSessions": [],
            "layoutName": self.layout_name,
            "customUrlParams": "",
            "targetUrl": self.target_url,
            "Referrer": "https://www.asroma.com/"
        }

        try:

            response = self.session.post(
                url,
                params=params,
                json=body,
                headers=headers,
                timeout=50
            )

            # ----------------------------------------------------
            # Controllo HTTP
            # ----------------------------------------------------

            if not response.ok:

                return (
                    False,
                    f"HTTP {response.status_code}: "
                    f"{response.text}"
                )

            data = response.json()

            # ----------------------------------------------------
            # Controllo Challenge
            # ----------------------------------------------------

            if data.get("challengeFailed"):

                return (
                    False,
                    "Blocco Challenge/Anti-bot attivo "
                    f"da Queue-it: {data}"
                )

            # ----------------------------------------------------
            # Recupero Queue ID
            # ----------------------------------------------------

            self.queue_id = data.get("queueId")

            if self.queue_id:

                return True, "OK"

            return (
                False,
                f"Risposta senza queueId: {data}"
            )

        except Exception as e:

            return (
                False,
                f"Eccezione Enqueue: {str(e)}"
            )

    # ============================================================
    # SESSION PARAMETERS
    # ============================================================

    def step_generate_session_params(self) -> bool:

        self.sets = int(time.time() * 1000)

        self.seid = str(uuid.uuid4())

        return True
