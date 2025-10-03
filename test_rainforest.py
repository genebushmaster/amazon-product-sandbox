#!/usr/bin/env python3
"""
Test script for Rainforest API handler
Tests fetching reviews for a hard-coded product
"""
from src.rainforest_handler import RainforestHandler
from src.utils import save_to_json
from loguru import logger
import json

def main():
    # Test product (Shimeyao 100 Pcs Peg Board Shelving Hooks)
    test_asin = "B09VXR9Y62"
    test_domain = "amazon.com.au"

    logger.info("Testing Rainforest API handler")
    logger.info(f"Test ASIN: {test_asin}")
    logger.info(f"Amazon Domain: {test_domain}")

    try:
        handler = RainforestHandler()

        # Test: Fetch product data (type=product)
        logger.info("\n=== Fetching product data ===")
        data = handler.get_product_data(asin=test_asin, amazon_domain=test_domain)

        if not data:
            logger.warning("No data returned")
            return

        # Save complete response to JSON
        save_to_json(data, "reviews_rainforest_test.json")
        logger.info("Saved data to data/reviews_rainforest_test.json")

        # Show product info
        product = data.get("product", {})
        if product:
            logger.info(f"\nProduct Info:")
            logger.info(f"  ASIN: {product.get('asin', 'N/A')}")
            logger.info(f"  Title: {product.get('title', 'N/A')}")
            logger.info(f"  Link: {product.get('link', 'N/A')}")
            logger.info(f"  Rating: {product.get('rating', 'N/A')}")
            logger.info(f"  Ratings Total: {product.get('ratings_total', 'N/A')}")
            logger.info(f"  Price: {product.get('buybox_winner', {}).get('price', {}).get('raw', 'N/A')}")

            # Show main image
            main_image = product.get("main_image", {})
            if main_image:
                logger.info(f"  Main Image: {main_image.get('link', 'N/A')}")

            # Show feature bullets
            feature_bullets = product.get("feature_bullets", [])
            if feature_bullets:
                logger.info(f"\n  Feature Bullets:")
                for i, bullet in enumerate(feature_bullets[:3], 1):
                    logger.info(f"    {i}. {bullet[:100]}...")

            # Show categories
            categories = product.get("categories", [])
            if categories:
                logger.info(f"\n  Categories:")
                for cat in categories[:3]:
                    logger.info(f"    - {cat.get('name', 'N/A')}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
