from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Dict, Any

PositionType = Literal['option', 'future']
OptionType = Literal['call', 'put']
Direction = Literal['long', 'short']

@dataclass
class Position:
    instrument_name: str
    position_type: PositionType
    direction: Direction
    size: float
    entry_price: float
    current_price: float
    timestamp: datetime
    leverage: Optional[float] = None
    option_type: Optional[OptionType] = None
    strike_price: Optional[float] = None
    expiration_date: Optional[datetime] = None
    
    @property
    def pnl(self) -> float:
        """Calculate position's profit/loss"""
        multiplier = 1 if self.direction == 'long' else -1
        return multiplier * (self.current_price - self.entry_price) * self.size
    
    @property
    def pnl_percentage(self) -> float:
        """Calculate position's profit/loss percentage"""
        return (self.pnl / (self.entry_price * self.size)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary format"""
        return {
            'instrument_name': self.instrument_name,
            'position_type': self.position_type,
            'direction': self.direction,
            'size': self.size,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'timestamp': self.timestamp,
            'leverage': self.leverage,
            'option_type': self.option_type,
            'strike_price': self.strike_price,
            'expiration_date': self.expiration_date
        }