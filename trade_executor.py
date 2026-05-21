import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from models import Trade, SessionLocal
from redis_manager import RedisPriceManager
from atm_calculator import ATMCalculator
from whatsapp_notifier import WhatsAppNotifier

class TradeExecutor:
    def __init__(self):
        self.redis_manager = RedisPriceManager()
        self.atm_calculator = ATMCalculator(strike_interval=50)
        self.whatsapp_notifier = WhatsAppNotifier()
        self.cooldown_seconds = 300
        self.last_trade_time = 0
    
    async def process_tick(self, ltp: float, timestamp: float):
        self.redis_manager.add_price(ltp, timestamp)
        
        spike_result = self.redis_manager.calculate_spike(ltp, timestamp)
        
        if spike_result is None:
            return
        
        spike_percentage, price_60s_ago = spike_result
        
        option_type = self.atm_calculator.get_option_type(spike_percentage)
        
        if option_type is None:
            return
        
        if timestamp - self.last_trade_time < self.cooldown_seconds:
            print(f"⏳ Cooldown active. Skipping trade. {int(self.cooldown_seconds - (timestamp - self.last_trade_time))}s remaining")
            return
        
        print(f"\n🔔 SPIKE DETECTED! {spike_percentage*100:.2f}%")
        print(f"   Current Price: {ltp}")
        print(f"   Price 60s ago: {price_60s_ago}")
        print(f"   Action: {option_type}")
        
        atm_strike = self.atm_calculator.calculate_atm_strike(ltp)
        entry_price = self.atm_calculator.simulate_premium(atm_strike, ltp, option_type)
        instrument = self.atm_calculator.get_option_instrument(atm_strike, option_type)
        
        print(f"   ATM Strike: {atm_strike}")
        print(f"   Instrument: {instrument}")
        print(f"   Entry Price: ₹{entry_price:.2f}")
        
        db = SessionLocal()
        try:
            trade = Trade(
                instrument=instrument,
                strike=atm_strike,
                type=option_type,
                entry_price=entry_price,
                timestamp=datetime.fromtimestamp(timestamp),
                spike_percentage=spike_percentage
            )
            
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            print(f"✅ Trade saved to database (ID: {trade.id})")
            
            await self.whatsapp_notifier.send_trade_alert(
                option_type=option_type,
                instrument=instrument,
                strike=atm_strike,
                entry_price=entry_price,
                spike_percentage=spike_percentage,
                timestamp=trade.timestamp
            )
            
            self.last_trade_time = timestamp
            
        except Exception as e:
            print(f"❌ Error executing trade: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def reset_cooldown(self):
        self.last_trade_time = 0
        print("✅ Trade cooldown reset")
