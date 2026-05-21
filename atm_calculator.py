import math

class ATMCalculator:
    def __init__(self, strike_interval: int = 50):
        self.strike_interval = strike_interval
    
    def calculate_atm_strike(self, current_price: float) -> int:
        rounded = round(current_price / self.strike_interval) * self.strike_interval
        return int(rounded)
    
    def get_option_type(self, spike_percentage: float) -> str:
        if spike_percentage >= 0.05:
            return "Long"
        elif spike_percentage <= -0.05:
            return "Short"
        return None
    
    def get_option_instrument(self, strike: int, option_type: str) -> str:
        if option_type == "Long":
            return f"NIFTY {strike} CE"
        elif option_type == "Short":
            return f"NIFTY {strike} PE"
        return None
    
    def simulate_premium(self, strike: int, current_price: float, option_type: str) -> float:
        if option_type == "Long":
            intrinsic_value = max(0, current_price - strike)
            time_value = abs(current_price - strike) * 0.02
            return intrinsic_value + time_value + 50
        elif option_type == "Short":
            intrinsic_value = max(0, strike - current_price)
            time_value = abs(current_price - strike) * 0.02
            return intrinsic_value + time_value + 50
        return 0.0
