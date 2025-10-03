#!/usr/bin/env python3
"""
Test script for Gemini API handler
Tests analyzing reviews using Rainforest product data and Apify reviews
"""
from src.gemini_handler import GeminiHandler
from src.utils import save_to_json
from loguru import logger
import json

def load_rainforest_product():
    """Load product info from Rainforest test results"""
    try:
        with open("data/reviews_rainforest_test.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("reviews_rainforest_test.json not found. Run test_rainforest.py first.")
        return None

def load_apify_reviews():
    """Load reviews from Apify test results"""
    try:
        with open("data/reviews_apify_test.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("reviews_apify_test.json not found. Run test_apify.py first.")
        return None

def main():
    logger.info("Testing Gemini API handler")

    # Load product data from Rainforest
    rainforest_data = load_rainforest_product()
    if not rainforest_data:
        return

    # Load reviews from Apify
    apify_reviews = load_apify_reviews()
    if not apify_reviews:
        return

    # Extract product info from Rainforest
    product_data = rainforest_data.get('product', {})
    product_title = product_data.get('title', 'Unknown Product')

    # Get feature bullets for description
    feature_bullets = product_data.get('feature_bullets', [])
    if feature_bullets:
        product_description = "\n".join([f"- {bullet}" for bullet in feature_bullets])
    else:
        product_description = product_data.get('description', 'No description available')

    logger.info(f"\nProduct (from Rainforest): {product_title[:80]}...")
    logger.info(f"Reviews (from Apify): {len(apify_reviews)} reviews")
    logger.info(f"Analyzing reviews...")

    try:
        handler = GeminiHandler()

        # Analyze reviews using Rainforest product data + Apify reviews
        result = handler.analyze_reviews(
            product_title=product_title,
            product_description=product_description,
            reviews=apify_reviews
        )

        if not result:
            logger.warning("No analysis returned")
            return

        # Save complete result
        save_to_json(result, "reviews_analysis_gemini_test.json")
        logger.info("Saved analysis to data/reviews_analysis_gemini_test.json")

        # Display analysis
        analysis_text = result.get('analysis', '')
        if analysis_text:
            logger.info("\n" + "="*80)
            logger.info("GEMINI ANALYSIS")
            logger.info("="*80)
            print(analysis_text)
            logger.info("="*80)
        else:
            logger.warning("No analysis text in result")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
