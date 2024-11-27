import requests
from typing import Dict, List, Any
from datetime import datetime
from ..config import Config
from ..models.position import Position

class DeribitClient:
    def __init__(self, test_mode: bool = True):
        self.base_url = Config.TEST_URL if test_mode else Config.PROD_URL
        self.access_token = None
        self.refresh_token = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Deribit API"""
        endpoint = "/api/v2/public/auth"
        data = {
            "grant_type": "client_credentials",
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET
        }
        
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        if response.status_code == 200:
            result = response.json()["result"]
            self.access_token = result["access_token"]
            self.refresh_token = result["refresh_token"]
        else:
            raise Exception("Authentication failed")

    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        endpoint = "/api/v2/private/get_positions"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"currency": "BTC"}
        
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
        if response.status_code != 200:
            raise Exception("Failed to fetch positions")
            
        positions = []
        result = response.json()["result"]
        
        for pos in result:
            position_type = 'option' if 'option' in pos['instrument_name'].lower() else 'future'
            
            position = Position(
                instrument_name=pos['instrument_name'],
                position_type=position_type,
                direction='long' if pos['size'] > 0 else 'short',
                size=abs(pos['size']),
                entry_price=pos['average_price'],
                current_price=pos['mark_price'],
                timestamp=datetime.fromtimestamp(pos['timestamp'] / 1000),
                leverage=pos.get('leverage'),
                option_type=pos.get('option_type'),
                strike_price=pos.get('strike'),
                expiration_date=datetime.fromtimestamp(pos['expiration_timestamp'] / 1000) if 'expiration_timestamp' in pos else None
            )
            positions.append(position)
            
        return positions