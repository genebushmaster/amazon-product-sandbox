#!/usr/bin/env python3
"""
Test script for BrightData API handler
Tests fetching reviews for a hard-coded product
"""
from src.brightdata_handler import BrightDataHandler
from src.utils import save_to_json
from loguru import logger

def main():
    # Test product (NearMoon Bath Towel Hooks)
    test_asin = "B092S3JWFM"
    test_url = "https://www.amazon.com.au/NearMoon-Stainless-Bathroom-Livingroom-Mounted-4/dp/B092S3JWFM/"

    logger.info("Testing BrightData API handler")
    logger.info(f"Test ASIN: {test_asin}")

    try:
        handler = BrightDataHandler()

        # Test 1: Fetch reviews by ASIN
        logger.info("\n=== Test 1: Fetching reviews by ASIN ===")
        reviews = handler.get_product_reviews(asin=test_asin, domain="amazon.com.au",
                                              limit_multiple_results=30)

        if reviews:
            logger.info(f"Successfully fetched {len(reviews)} reviews")

            # Save to JSON
            save_to_json(reviews, "reviews_output_test_by_asin.json")
            logger.info("Saved reviews to data/reviews_output_test_by_asin.json")

            # Show sample
            logger.info("\nSample review:")
            sample = reviews[0]
            logger.info(f"  Header: {sample.get('review_header')}")
            logger.info(f"  Rating: {sample.get('rating')}")
            logger.info(f"  Author: {sample.get('author_name')}")
            logger.info(f"  Date: {sample.get('review_posted_date')}")
            review_text = sample.get('review_text') or ""
            logger.info(f"  Text: {review_text[:200]}...")
        else:
            logger.warning("No reviews fetched")

        # Test 2: Fetch reviews by URL
        logger.info("\n=== Test 2: Fetching reviews by URL ===")
        reviews_from_url = handler.get_reviews_from_url(amazon_url=test_url)

        if reviews_from_url:
            logger.info(f"Successfully fetched {len(reviews_from_url)} reviews from URL")
            save_to_json(reviews_from_url, "reviews_output_test_by_url.json")
            logger.info("Saved reviews to data/reviews_output_test_by_url.json")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
