import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CLIENT_ID = os.getenv('DERIBIT_CLIENT_ID')
    CLIENT_SECRET = os.getenv('DERIBIT_CLIENT_SECRET')
    TEST_URL = os.getenv('DERIBIT_TEST_URL')
    PROD_URL = os.getenv('DERIBIT_PROD_URL')
    
    # Trading parameters
    BTC_MIN_TRADE_SIZE = 0.0001
    POSITION_UPDATE_INTERVAL = 60  # seconds
    
    # Risk parameters
    MAX_POSITION_SIZE = 1.0  # BTC
    MAX_LEVERAGE = 20
    STOP_LOSS_PERCENTAGE = 0.10  # 10%
    
    # Reporting parameters
    REPORT_TIMEFRAMES = ['1H', '4H', '1D', '1W']