from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import threading
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from models import Trade, init_db, get_db
from dhan_websocket import DhanWebSocketHandler
from trade_executor import TradeExecutor
from redis_manager import RedisPriceManager
from atm_calculator import ATMCalculator

app = FastAPI(
    title="Instant Strike Execution Engine",
    description="Real-time NIFTY 50 spike detection and ATM option trading system",
    version="1.0.0"
)

trade_executor = TradeExecutor()
websocket_handler = None
websocket_thread = None

class TradeResponse(BaseModel):
    id: int
    instrument: str
    strike: int
    type: str
    entry_price: float
    timestamp: datetime
    spike_percentage: Optional[float]
    
    class Config:
        from_attributes = True

class SystemStatus(BaseModel):
    websocket_connected: bool
    redis_price_count: int
    total_trades: int
    last_trade: Optional[TradeResponse]

@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Instant Strike Execution Engine...")
    init_db()
    print("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    global websocket_handler
    if websocket_handler:
        websocket_handler.stop()
    print("👋 Shutdown complete")

def run_websocket():
    global websocket_handler
    try:
        websocket_handler.start()
    except Exception as e:
        print(f"❌ WebSocket thread error: {str(e)}")

@app.post("/start", response_model=dict)
async def start_trading(background_tasks: BackgroundTasks):
    global websocket_handler, websocket_thread
    
    if websocket_handler and websocket_handler.is_running:
        return {"status": "already_running", "message": "Trading system is already active"}
    
    websocket_handler = DhanWebSocketHandler(
        on_tick_callback=trade_executor.process_tick
    )
    
    websocket_handler.event_loop = asyncio.get_event_loop()
    
    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    websocket_thread.start()
    
    return {
        "status": "started",
        "message": "Trading system started successfully",
        "monitoring": "NIFTY 50 (Security ID: 13)",
        "spike_threshold": "±5%",
        "window": "60 seconds"
    }

@app.post("/stop", response_model=dict)
async def stop_trading():
    global websocket_handler
    
    if not websocket_handler or not websocket_handler.is_running:
        return {"status": "not_running", "message": "Trading system is not active"}
    
    websocket_handler.stop()
    
    return {
        "status": "stopped",
        "message": "Trading system stopped successfully"
    }

@app.get("/status", response_model=SystemStatus)
async def get_status(db: Session = Depends(get_db)):
    redis_manager = RedisPriceManager()
    
    total_trades = db.query(Trade).count()
    last_trade = db.query(Trade).order_by(Trade.timestamp.desc()).first()
    
    return SystemStatus(
        websocket_connected=websocket_handler.is_running if websocket_handler else False,
        redis_price_count=redis_manager.get_price_count(),
        total_trades=total_trades,
        last_trade=TradeResponse.from_orm(last_trade) if last_trade else None
    )

@app.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).offset(skip).limit(limit).all()
    return [TradeResponse.from_orm(trade) for trade in trades]

@app.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeResponse.from_orm(trade)

@app.post("/reset-cooldown", response_model=dict)
async def reset_cooldown():
    trade_executor.reset_cooldown()
    return {"status": "success", "message": "Trade cooldown reset"}

@app.delete("/clear-redis", response_model=dict)
async def clear_redis():
    redis_manager = RedisPriceManager()
    redis_manager.clear_all()
    return {"status": "success", "message": "Redis price data cleared"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Instant Strike Execution Engine"
    }

@app.get("/")
async def root():
    return {
        "service": "Instant Strike Execution Engine",
        "version": "1.0.0",
        "description": "Real-time NIFTY 50 spike detection and ATM option trading",
        "endpoints": {
            "start": "POST /start - Start the trading system",
            "stop": "POST /stop - Stop the trading system",
            "status": "GET /status - Get system status",
            "trades": "GET /trades - List all trades",
            "health": "GET /health - Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
