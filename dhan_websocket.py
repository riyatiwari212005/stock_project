import asyncio
import time
from datetime import datetime
from dhanhq import marketfeed
from typing import Callable, Optional
import os

class DhanWebSocketHandler:
    def __init__(
        self,
        client_id: str = None,
        access_token: str = None,
        on_tick_callback: Optional[Callable] = None
    ):
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN")
        self.on_tick_callback = on_tick_callback
        self.instruments = [(0, "13")]
        self.data = None
        self.is_running = False
        self.event_loop = None
        
    def on_connect(self, instance):
        print("✅ Connected to Dhan WebSocket")
        print(f"📡 Subscribing to NIFTY 50 (Security ID: 13)")
        instance.subscribe_symbols(self.instruments)
    
    def on_message(self, instance, message):
        if message and isinstance(message, dict):
            try:
                ltp = message.get('LTP') or message.get('last_price')
                
                if ltp:
                    timestamp = time.time()
                    
                    print(f"📊 Tick received - LTP: {ltp}, Time: {datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')}")
                    
                    if self.on_tick_callback and self.event_loop:
                        asyncio.run_coroutine_threadsafe(
                            self.on_tick_callback(ltp, timestamp),
                            self.event_loop
                        )
                        
            except Exception as e:
                print(f"❌ Error processing message: {str(e)}")
    
    def start(self):
        if not self.client_id or not self.access_token:
            raise ValueError("Dhan Client ID and Access Token are required")
        
        print("🚀 Starting Dhan WebSocket connection...")
        
        try:
            self.data = marketfeed.DhanFeed(
                self.client_id,
                self.access_token,
                self.instruments
            )
            
            self.data.on_connect = self.on_connect
            self.data.on_message = self.on_message
            
            self.is_running = True
            self.data.run_forever()
            
        except Exception as e:
            print(f"❌ WebSocket error: {str(e)}")
            self.is_running = False
            raise
    
    def stop(self):
        if self.data:
            print("🛑 Stopping Dhan WebSocket connection...")
            self.data.close_connection()
            self.is_running = False
