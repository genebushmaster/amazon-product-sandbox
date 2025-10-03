import json
import pandas as pd
from typing import List, Dict
from loguru import logger
from .models import Product, SearchResult

def save_to_json(data: List[Dict], filename: str, output_dir: str = "data") -> None:
    try:
        with open(f"{output_dir}/{filename}", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {output_dir}/{filename}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")

def save_to_csv(data: List[Dict], filename: str) -> None:
    try:
        df = pd.DataFrame(data)
        df.to_csv(f"data/{filename}", index=False)
        logger.info(f"Data saved to data/{filename}")
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")

def parse_products(raw_results: List[Dict]) -> List[Product]:
    products = []
    for item in raw_results:
        try:
            product = Product(
                title=item.get("title", ""),
                price=item.get("price", ""),
                rating=item.get("rating"),
                reviews_count=item.get("reviews"),
                url=item.get("link"),
                image_url=item.get("thumbnail"),
                source=item.get("source"),
                product_id=item.get("product_id")
            )
            products.append(product)
        except Exception as e:
            logger.warning(f"Failed to parse product: {e}")
            continue
    return products