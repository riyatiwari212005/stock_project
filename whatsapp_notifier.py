import httpx
import os
from datetime import datetime
from typing import Optional

class WhatsAppNotifier:
    def __init__(self, webhook_url: str = None, api_key: str = None):
        self.webhook_url = webhook_url or os.getenv("WHATSAPP_WEBHOOK_URL")
        self.api_key = api_key or os.getenv("WHATSAPP_API_KEY")
        self.phone_number = os.getenv("WHATSAPP_PHONE_NUMBER")
    
    async def send_trade_alert(
        self,
        option_type: str,
        instrument: str,
        strike: int,
        entry_price: float,
        spike_percentage: float,
        timestamp: datetime
    ) -> bool:
        if not self.webhook_url:
            print("⚠️ WhatsApp webhook URL not configured. Skipping notification.")
            return False
        
        direction = "Long" if option_type == "Long" else "Short"
        option_suffix = "CE" if option_type == "Long" else "PE"
        spike_direction = "+" if spike_percentage > 0 else ""
        
        message = (
            f"📊 Trade Alert!\n\n"
            f"{direction} NIFTY {strike} {option_suffix}\n"
            f"Entry Price: ₹{entry_price:.2f}\n"
            f"Time: {timestamp.strftime('%H:%M:%S')}\n"
            f"Reason: {spike_direction}{spike_percentage*100:.2f}% Spike"
        )
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "phone": self.phone_number,
                    "message": message
                }
                
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✅ WhatsApp notification sent successfully")
                    return True
                else:
                    print(f"❌ WhatsApp notification failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending WhatsApp notification: {str(e)}")
            return False
    
    def send_trade_alert_sync(
        self,
        option_type: str,
        instrument: str,
        strike: int,
        entry_price: float,
        spike_percentage: float,
        timestamp: datetime
    ) -> bool:
        if not self.webhook_url:
            print("⚠️ WhatsApp webhook URL not configured. Skipping notification.")
            return False
        
        direction = "Long" if option_type == "Long" else "Short"
        option_suffix = "CE" if option_type == "Long" else "PE"
        spike_direction = "+" if spike_percentage > 0 else ""
        
        message = (
            f"📊 Trade Alert!\n\n"
            f"{direction} NIFTY {strike} {option_suffix}\n"
            f"Entry Price: ₹{entry_price:.2f}\n"
            f"Time: {timestamp.strftime('%H:%M:%S')}\n"
            f"Reason: {spike_direction}{spike_percentage*100:.2f}% Spike"
        )
        
        try:
            with httpx.Client() as client:
                payload = {
                    "phone": self.phone_number,
                    "message": message
                }
                
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✅ WhatsApp notification sent successfully")
                    return True
                else:
                    print(f"❌ WhatsApp notification failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending WhatsApp notification: {str(e)}")
            return False
