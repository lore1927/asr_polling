#!/usr/bin/env python3
import requests
import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

class QueueItAutomation:
    """Automazione del flusso Queue-it per AS Roma"""
    
    BASE_URL = "https://bestunion.queue-it.net"
    CUSTOMER_ID = "bestunion"
    
    def __init__(
        self, 
        vendor: str = "webroma", 
        language: str = "IT", 
        target_url: str = None, 
        event_id: str = "asrabbonamenti2022", 
        is_waiting_list: bool = False,
        layout_version: int = 180105136056
    ):
        self.vendor = vendor
        self.language = language
        self.session = requests.Session()
        self.EVENT_ID = event_id
        self.layout_version = int(layout_version)
        
        # Gestione dell'URL Target con pulizia di eventuali query params preesistenti
        base_target = target_url.split("?")[0] if target_url else "https://biglietti.asroma.com/tickets/season/pre/MAN132/D19"

        if is_waiting_list:
            self.target_url = f"{base_target}?lang={language}&promo=WLIST&vendor=venpre"
        else:
            self.target_url = f"{base_target}?lang={language}&vendor={vendor}"
        
        self.queue_id: Optional[str] = None
        self.seid: Optional[str] = None
        self.sets: Optional[int] = None
        self.redirect_url: Optional[str] = None
        
        print(f"[*] Automazione pronta sul target: {self.target_url} | LayoutVersion: {self.layout_version}")

    def log(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] | {message}")

    def step_enqueue(self) -> Tuple[bool, str]:
        url = f"{self.BASE_URL}/spa-api/queue/{self.CUSTOMER_ID}/{self.EVENT_ID}/enqueue"
        params = {"cid": "it-IT", "l": "Asroma prod Abbonamenti", "t": self.target_url}
        body = {
            "challengeSessions": [],
            "layoutName": "Asroma prod Abbonamenti",
            "customUrlParams": "",
            "targetUrl": self.target_url,
            "Referrer": "https://www.asroma.com/"
        }
        try:
            response = self.session.post(url, params=params, json=body, timeout=50)
            if not response.ok:
                return False, f"HTTP {response.status_code}: {response.text}"
                
            data = response.json()
            self.queue_id = data.get("queueId")
            
            if self.queue_id:
                return True, "OK"
            else:
                return False, f"queueId non presente nella risposta: {data}"
        except Exception as e:
            return False, f"Eccezione Enqueue: {str(e)}"

    def step_generate_session_params(self) -> bool:
        self.sets = int(time.time() * 1000)
        self.seid = str(uuid.uuid4())
        return True
