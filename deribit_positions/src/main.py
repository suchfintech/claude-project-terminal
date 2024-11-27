from services.deribit_client import DeribitClient
from reporting.position_reporter import PositionReporter
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize Deribit client
        client = DeribitClient(test_mode=True)
        
        # Fetch positions
        positions = client.get_positions()
        logger.info(f"Fetched {len(positions)} positions")
        
        # Generate reports
        reporter = PositionReporter(positions)
        
        # Generate summary report
        report = reporter.generate_summary_report()
        logger.info("Generated summary report")
        
        # Export to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporter.export_to_csv(f"position_report_{timestamp}.csv")
        logger.info(f"Exported report to CSV")
        
        # Generate and save position distribution plot
        fig = reporter.plot_position_distribution()
        fig.write_html(f"position_distribution_{timestamp}.html")
        logger.info("Generated position distribution plot")
        
        # Print summary
        print("\nPortfolio Summary:")
        for key, value in report['portfolio_metrics'].items():
            print(f"{key}: {value}")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()