import redis
import json
import time
from typing import Optional, Tuple
import os

class RedisPriceManager:
    def __init__(self, host: str = None, port: int = None, db: int = 0):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.db = db
        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )
        self.price_key = "nifty:prices"
        self.window_seconds = 60
    
    def add_price(self, price: float, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()
        
        self.redis_client.zadd(
            self.price_key,
            {json.dumps({"price": price, "ts": timestamp}): timestamp}
        )
        
        cutoff_time = timestamp - self.window_seconds - 10
        self.redis_client.zremrangebyscore(self.price_key, "-inf", cutoff_time)
    
    def get_price_60s_ago(self, current_timestamp: float = None) -> Optional[float]:
        if current_timestamp is None:
            current_timestamp = time.time()
        
        target_time = current_timestamp - self.window_seconds
        
        results = self.redis_client.zrangebyscore(
            self.price_key,
            target_time - 2,
            target_time + 2,
            withscores=True
        )
        
        if not results:
            return None
        
        closest_entry = min(results, key=lambda x: abs(x[1] - target_time))
        data = json.loads(closest_entry[0])
        return data["price"]
    
    def calculate_spike(self, current_price: float, current_timestamp: float = None) -> Optional[Tuple[float, float]]:
        if current_timestamp is None:
            current_timestamp = time.time()
        
        price_60s_ago = self.get_price_60s_ago(current_timestamp)
        
        if price_60s_ago is None:
            return None
        
        spike_percentage = (current_price - price_60s_ago) / price_60s_ago
        
        return spike_percentage, price_60s_ago
    
    def clear_all(self):
        self.redis_client.delete(self.price_key)
    
    def get_price_count(self) -> int:
        return self.redis_client.zcard(self.price_key)
