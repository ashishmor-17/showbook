import os
import sys
import httpx
import structlog
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from dotenv import load_dotenv

# Make sure apps/scraper is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from root .env file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(base_dir, ".env"))

from showbook_common.logger import setup_logging

# Initialize common logging
setup_logging(service_name="scraper-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = structlog.get_logger(__name__)

def run_scraper():
    logger.info("starting_scrapy_crawler_process")
    
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "scraper.settings")
    settings = get_project_settings()
    
    process = CrawlerProcess(settings)
    process.crawl("tmdb")
    process.start() # Blocks until crawling is complete
    
    logger.info("scrapy_crawler_process_completed")

def trigger_ingestion():
    catalog_url = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8000")
    trigger_endpoint = f"{catalog_url}/api/v1/admin/catalog/ingestion/trigger"
    
    scraped_file = os.path.join(base_dir, "data", "raw_scraped", "movies_scraped.json")
    
    logger.info("triggering_catalog_ingestion_pipeline", url=trigger_endpoint, file_path=scraped_file)
    
    payload = {
        "source": "SCRAPER",
        "file_path": scraped_file
    }
    
    try:
        response = httpx.post(trigger_endpoint, json=payload, timeout=60.0)
        response.raise_for_status()
        logger.info("catalog_ingestion_pipeline_triggered_successfully", response=response.json())
    except Exception as e:
        logger.error("failed_to_trigger_catalog_ingestion_pipeline", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    run_scraper()
    trigger_ingestion()
