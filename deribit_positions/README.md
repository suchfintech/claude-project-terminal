# Deribit Positions Risk Analysis System

A Python-based system for analyzing and reporting risk metrics for Bitcoin positions (Options and Futures) on Deribit exchange.

## Features

- **Position Tracking**
  - Real-time position monitoring
  - Support for both Options and Futures
  - Historical position data tracking

- **Risk Analysis**
  - Value at Risk (VaR) calculation
  - Greeks analysis for options (Delta, Gamma, Theta, Vega)
  - Maximum drawdown estimation
  - Leverage risk assessment
  - Portfolio correlation analysis

- **Portfolio Analytics**
  - Total portfolio value
  - Profit and Loss (PnL) tracking
  - Position diversity metrics
  - Risk concentration analysis

- **Reporting**
  - Automated report generation
  - Position distribution visualizations
  - Risk metric dashboards
  - CSV export functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/deribit_positions.git
cd deribit_positions
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your Deribit API credentials.

## Configuration

The system can be configured through `src/config.py` and environment variables:

- `DERIBIT_API_KEY`: Your Deribit API key
- `DERIBIT_API_SECRET`: Your Deribit API secret
- `RISK_THRESHOLD`: Custom risk threshold for alerts
- `REPORT_INTERVAL`: Reporting frequency in minutes

## Usage

Run the main script to start the analysis:

```bash
python src/main.py
```

### Available Commands

- `--report`: Generate a one-time report
- `--monitor`: Start continuous monitoring
- `--backtest`: Run historical analysis
- `--export`: Export data to CSV

Example:
```bash
python src/main.py --report --export
```

## Risk Metrics

### Position-Level Metrics
- Value at Risk (VaR)
- Maximum potential loss
- Greeks (for options)
- Leverage ratio
- Position size relative to portfolio

### Portfolio-Level Metrics
- Portfolio VaR
- Correlation matrix
- Risk concentration
- Total exposure
- Sharpe ratio

## Report Types

1. **Summary Report**
   - Overview of all positions
   - Key risk metrics
   - Portfolio statistics

2. **Detailed Position Report**
   - Individual position analysis
   - Risk breakdown
   - Historical performance

3. **Risk Alert Report**
   - Positions exceeding risk thresholds
   - Leverage warnings
   - Correlation alerts

## Data Export

Data can be exported in various formats:
- CSV files
- JSON format
- Excel spreadsheets
- PDF reports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

- API keys are stored securely in environment variables
- Rate limiting is implemented for API calls
- Data validation for all inputs
- Secure error handling

## Support

For support, please:
1. Check the documentation
2. Create an issue in the repository
3. Contact the maintainers

## Disclaimer

This tool is for informational purposes only. Always verify the calculations and consult with financial advisors for trading decisions.
