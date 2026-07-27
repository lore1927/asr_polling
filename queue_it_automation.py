#!/usr/bin/env python3
import requests
import uuid
import time
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse

class QueueItAutomation:
    """Automazione del flusso Queue-it per AS Roma"""
    
    BASE_URL = "https://bestunion.queue-it.net"
    CUSTOMER_ID = "bestunion"
    
    def __init__(self, vendor: str = "webroma", language: str = "IT", target_url: str = None, event_id: str = "asrabbonamenti2022", is_waiting_list: bool = False):
        self.vendor = vendor
        self.language = language
        self.session = requests.Session()
        self.EVENT_ID = event_id
        
        # Costruzione parametri query string per l'URL target
        params = {
            "lang": language
        }
        
        if is_waiting_list:
            params["promo"] = "WLIST"
            params["vendor"] = "venpre"
        else:
            params["vendor"] = vendor

        query_string = urlencode(params)
        
        # Se viene passato un URL specifico dai bottoni usa quello, altrimenti usa il default
        base = target_url if target_url else "https://biglietti.asroma.com/tickets/season/pre/MAN132/D19"
        
        # Gestisce la presenza di eventuali query params già esistenti nell'URL base
        separator = "&" if "?" in base else "?"
        self.target_url = f"{base}{separator}{query_string}"
        
        self.queue_id: Optional[str] = None
        self.seid: Optional[str] = None
        self.sets: Optional[int] = None
        self.redirect_url: Optional[str] = None
        
        print(f"[*] Automazione pronta sul target: {self.target_url}")
    
    def log(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] | {message}")
    
    def step_enqueue(self) -> bool:
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
            response.raise_for_status()
            data = response.json()
            self.queue_id = data.get("queueId")
            return True if self.queue_id else False
        except Exception as e:
            self.log("ERROR", f"Errore Enqueue: {str(e)}")
            return False
    
    def step_generate_session_params(self) -> bool:
        self.sets = int(time.time() * 1000)
        self.seid = str(uuid.uuid4())
        return True
    
    def step_status_polling(self, max_attempts: int = 450, poll_interval: int = 2) -> bool:
        url = f"{self.BASE_URL}/spa-api/queue/{self.CUSTOMER_ID}/{self.EVENT_ID}/{self.queue_id}/status"
        
        for attempt in range(1, max_attempts + 1):
            try:
                params = {
                    "cid": "it-IT", "l": "Asroma prod Abbonamenti",
                    "t": self.target_url, "seid": self.seid, "sets": self.sets
                }
                body = {
                    "targetUrl": self.target_url, "customUrlParams": "", "layoutVersion": 180105136056,
                    "layoutName": "Asroma prod Abbonamenti", "isClientRedayToRedirect": False, "isBeforeOrIdle": False
                }
                response = self.session.post(url, params=params, json=body, timeout=50)
                response.raise_for_status()
                data = response.json()
                
                if "redirectUrl" in data and data.get("isRedirectToTarget"):
                    self.redirect_url = data["redirectUrl"]
                    return True
                
                time.sleep(poll_interval)
            except Exception:
                time.sleep(poll_interval)
        return False
    
    def extract_parameters(self) -> Dict[str, str]:
        if not self.redirect_url: return {}
        parsed = urlparse(self.redirect_url)
        params = parse_qs(parsed.query)
        return {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
    
    def run(self, max_polling_attempts: int = 450) -> Tuple[bool, Optional[str]]:
        if not self.step_enqueue(): return False, None
        if not self.step_generate_session_params(): return False, None
        if not self.step_status_polling(max_attempts=max_polling_attempts): return False, None
        return True, self.redirect_url
