from typing import List, Dict
import numpy as np
from ..models.position import Position

class RiskCalculator:
    @staticmethod
    def calculate_position_risks(position: Position) -> Dict[str, float]:
        """Calculate various risk metrics for a position"""
        value = position.size * position.current_price
        
        # Calculate Value at Risk (VaR) using historical volatility
        # This is a simplified version - you might want to use more sophisticated methods
        daily_var_95 = value * 0.1  # Assuming 10% daily VaR at 95% confidence
        
        # Calculate maximum loss
        max_loss = float('inf')
        if position.position_type == 'option':
            if position.direction == 'long':
                max_loss = value  # Maximum loss is premium paid
            else:
                max_loss = float('inf')  # Theoretically unlimited for short options
        elif position.position_type == 'future':
            if position.leverage:
                max_loss = value / position.leverage
            else:
                max_loss = value
        
        return {
            'position_value': value,
            'daily_var_95': daily_var_95,
            'max_loss': max_loss,
            'leverage_risk': position.leverage if position.leverage else 1.0,
            'liquidation_risk': 'high' if (position.leverage or 1.0) > 10 else 'medium' if (position.leverage or 1.0) > 5 else 'low'
        }

    @staticmethod
    def calculate_portfolio_metrics(positions: List[Position]) -> Dict[str, float]:
        """Calculate portfolio-wide risk metrics"""
        total_value = sum(pos.size * pos.current_price for pos in positions)
        total_pnl = sum(pos.pnl for pos in positions)
        
        # Calculate portfolio diversity score
        position_types = set(pos.position_type for pos in positions)
        diversity_score = len(position_types) / 2  # Normalized by maximum possible types
        
        return {
            'total_value': total_value,
            'total_pnl': total_pnl,
            'pnl_percentage': (total_pnl / total_value) * 100 if total_value else 0,
            'diversity_score': diversity_score,
            'position_count': len(positions)
        }