import os
import json
from scrapy import Spider

class JsonWriterPipeline:
    def __init__(self) -> None:
        self.movies = []

    def open_spider(self, spider: Spider) -> None:
        self.movies = []

    def process_item(self, item: dict, spider: Spider) -> dict:
        self.movies.append(item)
        return item

    def close_spider(self, spider: Spider) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        output_dir = os.path.join(base_dir, "data", "raw_scraped")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "movies_scraped.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.movies, f, indent=2, ensure_ascii=False)
            
        spider.logger.info(f"Successfully wrote {len(self.movies)} items to {output_file}")
