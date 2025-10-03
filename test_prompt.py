#!/usr/bin/env python3
"""
Test script to preview Gemini prompt without calling API
"""
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
    logger.info("Building Gemini prompt preview")

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

    logger.info(f"\nProduct: {product_title}")
    logger.info(f"Reviews: {len(apify_reviews)} reviews")

    # Build reviews text (same logic as gemini_handler)
    reviews_text = []
    for review in apify_reviews:
        rating = review.get('ratingScore', review.get('rating', 'N/A'))
        description = review.get('reviewDescription', review.get('text', review.get('body', '')))
        if description:
            reviews_text.append(f"{rating}: {description}")

    reviews_combined = "\n".join(reviews_text)

    # Construct prompt (same as gemini_handler)
    prompt = f"""You are evaluating the product "{product_title}" with the following product description:
{product_description}

Customers have reviewed this product with these reviews:
{reviews_combined}

Your goal is to provide a list of top product strengths and top product concerns, listed from most common to least common.

Requirements:
- Each list (strengths and concerns) should have a maximum of 10 points and a minimum of 3 points
- List items should be concise and specific
- Focus on the most commonly mentioned themes across reviews
- Base your analysis only on the reviews provided

Please provide your response in the following format:

**Product Strengths:**
1. [strength]
2. [strength]
...

**Product Concerns:**
1. [concern]
2. [concern]
..."""

    # Output prompt
    print("\n" + "="*80)
    print("PROMPT PREVIEW")
    print("="*80)
    print(prompt)
    print("="*80)
    print(f"\nPrompt length: {len(prompt)} characters")
    print(f"Reviews included: {len(reviews_text)} reviews")

if __name__ == "__main__":
    main()
