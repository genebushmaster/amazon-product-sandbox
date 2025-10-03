#!/usr/bin/env python3
"""
Test script for Apify API handler
Tests fetching reviews for a hard-coded product
"""
from src.apify_handler import ApifyHandler
from src.utils import save_to_json
from loguru import logger

def main():
    # Test product (Shimeyao 100 Pcs Peg Board Shelving Hooks)
    test_asin = "B09VXR9Y62"
    test_domain = "amazon.com.au"

    logger.info("Testing Apify API handler")
    logger.info(f"Test ASIN: {test_asin}")
    logger.info(f"Amazon Domain: {test_domain}")

    try:
        handler = ApifyHandler()

        # Test: Fetch product reviews
        logger.info("\n=== Fetching product reviews ===")
        reviews = handler.get_product_reviews(
            asin=test_asin,
            amazon_domain=test_domain,
            max_reviews=20  # Limit to 20 reviews for testing
        )

        if not reviews:
            logger.warning("No reviews returned")
            return

        logger.info(f"\nFetched {len(reviews)} reviews")

        # Save complete response to JSON
        save_to_json(reviews, "reviews_apify_test.json")
        logger.info("Saved data to data/reviews_apify_test.json")

        # Show sample review
        if reviews and len(reviews) > 0:
            logger.info("\nSample review:")
            sample = reviews[0]
            logger.info(f"  Review Title: {sample.get('reviewTitle', 'N/A')}")
            logger.info(f"  Rating: {sample.get('ratingScore', 'N/A')}")
            logger.info(f"  Date: {sample.get('date', 'N/A')}")
            logger.info(f"  Verified: {sample.get('isVerified', 'N/A')}")
            logger.info(f"  Amazon Vine: {sample.get('isAmazonVine', 'N/A')}")
            review_text = sample.get('reviewDescription', '')
            if review_text:
                logger.info(f"  Description: {review_text[:200]}...")

            # Show product info
            logger.info(f"\n  Product ASIN: {sample.get('productAsin', 'N/A')}")
            logger.info(f"  Variant ASIN: {sample.get('variantAsin', 'N/A')}")
            logger.info(f"  Review URL: {sample.get('reviewUrl', 'N/A')}")

            # Show images if available
            images = sample.get('reviewImages', [])
            if images:
                logger.info(f"  Review has {len(images)} image(s)")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
