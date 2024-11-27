from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from ..models.position import Position
from ..analysis.risk_calculator import RiskCalculator

class PositionReporter:
    def __init__(self, positions: List[Position]):
        self.positions = positions
        self.risk_calculator = RiskCalculator()

    def generate_summary_report(self) -> Dict:
        """Generate a summary report of all positions"""
        portfolio_metrics = self.risk_calculator.calculate_portfolio_metrics(self.positions)
        
        position_summaries = []
        for position in self.positions:
            risks = self.risk_calculator.calculate_position_risks(position)
            position_data = position.to_dict()
            position_data.update(risks)
            position_summaries.append(position_data)
        
        return {
            'timestamp': datetime.now(),
            'portfolio_metrics': portfolio_metrics,
            'positions': position_summaries
        }

    def plot_position_distribution(self) -> go.Figure:
        """Create a visual representation of position distribution"""
        df = pd.DataFrame([p.to_dict() for p in self.positions])
        
        fig = go.Figure()
        
        # Add position sizes
        fig.add_trace(go.Bar(
            x=df['instrument_name'],
            y=df['size'],
            name='Position Size'
        ))
        
        # Add PnL
        fig.add_trace(go.Scatter(
            x=df['instrument_name'],
            y=df['pnl'],
            name='PnL',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Position Distribution and PnL',
            yaxis=dict(title='Position Size (BTC)'),
            yaxis2=dict(title='PnL', overlaying='y', side='right'),
            barmode='group'
        )
        
        return fig

    def export_to_csv(self, filename: str):
        """Export position data to CSV"""
        report = self.generate_summary_report()
        df = pd.DataFrame(report['positions'])
        df.to_csv(filename, index=False)