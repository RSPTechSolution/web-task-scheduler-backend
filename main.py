import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import start_scheduler
from dashboard.app import app
from services.logger import logger

if __name__ == "__main__":
    logger.info("Starting Web Automation System...")

    # Start the background scheduler
    start_scheduler()

    # Start the Flask Dashboard
    # We set debug=False for production/VM
    app.run(host='0.0.0.0', port=5000, debug=False)
