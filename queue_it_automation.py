#!/usr/bin/env python3
import requests
import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

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
        
        # Header per simulare un browser reale (Chrome su Windows)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://bestunion.queue-it.net",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        
        self.EVENT_ID = event_id
        self.layout_version = int(layout_version)
        
        # Gestione URL Target
        base_target = target_url.split("?")[0] if target_url else "https://biglietti.asroma.com/tickets/season/pre/MAN132/D19"

        if is_waiting_list:
            self.target_url = f"{base_target}?lang={language}&promo=WLIST&vendor=venpre"
        else:
            self.target_url = f"{base_target}?lang={language}&vendor={vendor}"
        
        self.queue_id: Optional[str] = None
        self.seid: Optional[str] = None
        self.sets: Optional[int] = None
        self.redirect_url: Optional[str] = None

    def step_enqueue(self) -> Tuple[bool, str]:
        url = f"{self.BASE_URL}/spa-api/queue/{self.CUSTOMER_ID}/{self.EVENT_ID}/enqueue"
        
        # Referrer dinamico basato sull'URL della coda reale Queue-it
        queue_page_url = f"{self.BASE_URL}/?c={self.CUSTOMER_ID}&e={self.EVENT_ID}&cid={self.language.lower()}-{self.language.upper()}&t={self.target_url}"
        
        headers = {
            "Referer": queue_page_url
        }
        
        params = {
            "cid": "it-IT",
            "l": "Asroma prod Abbonamenti",
            "t": self.target_url
        }
        
        body = {
            "challengeSessions": [],
            "layoutName": "Asroma prod Abbonamenti",
            "customUrlParams": "",
            "targetUrl": self.target_url,
            "Referrer": "https://www.asroma.com/"
        }
        
        try:
            response = self.session.post(url, params=params, json=body, headers=headers, timeout=50)
            
            if not response.ok:
                return False, f"HTTP {response.status_code}: {response.text}"
                
            data = response.json()
            
            # Se la challenge fallisce, verifichiamo la risposta
            if data.get("challengeFailed"):
                return False, f"Blocco Challenge/Anti-bot attivo da Queue-it: {data}"
                
            self.queue_id = data.get("queueId")
            
            if self.queue_id:
                return True, "OK"
            else:
                return False, f"Risposta senza queueId: {data}"
                
        except Exception as e:
            return False, f"Eccezione Enqueue: {str(e)}"

    def step_generate_session_params(self) -> bool:
        self.sets = int(time.time() * 1000)
        self.seid = str(uuid.uuid4())
        return True
