import os
import requests
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class GeminiHandler:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.5-flash"
        logger.info("Gemini API handler initialized")

    def analyze_reviews(self, product_title: str, product_description: str,
                       reviews: List[Dict]) -> Optional[Dict]:
        """
        Analyze product reviews using Gemini AI

        Args:
            product_title: Product title/name
            product_description: Product description or features
            reviews: List of review dictionaries with 'ratingScore' and 'reviewDescription'

        Returns:
            Dictionary containing analysis results with 'strengths' and 'concerns'
        """
        # Build reviews text
        reviews_text = []
        for review in reviews:
            rating = review.get('ratingScore', review.get('rating', 'N/A'))
            description = review.get('reviewDescription', review.get('text', review.get('body', '')))
            if description:
                reviews_text.append(f"{rating}: {description}")

        reviews_combined = "\n".join(reviews_text)

        # Construct prompt
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

        # Prepare API request
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            logger.info(f"Analyzing {len(reviews)} reviews for product: {product_title[:50]}...")
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

            data = response.json()

            # Extract generated text from response
            candidates = data.get("candidates", [])
            if not candidates:
                logger.error("No candidates in response")
                return None

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                logger.error("No parts in response")
                return None

            generated_text = parts[0].get("text", "")

            if generated_text:
                logger.info("Analysis completed successfully")
                return {
                    "analysis": generated_text,
                    "raw_response": data
                }
            else:
                logger.error("No text generated")
                return None

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def analyze_reviews_simple(self, reviews: List[Dict],
                              product_info: Dict = None) -> Optional[str]:
        """
        Simplified version that extracts product info from reviews if not provided

        Args:
            reviews: List of review dictionaries
            product_info: Optional dict with 'title' and 'description'

        Returns:
            Generated analysis text
        """
        # Extract product info from first review if not provided
        if not product_info and reviews:
            first_review = reviews[0]
            product_data = first_review.get('product', {})
            product_info = {
                'title': product_data.get('title', 'Unknown Product'),
                'description': product_data.get('feature_bullets_flat',
                              product_data.get('description', 'No description available'))
            }

        if not product_info:
            logger.error("No product info available")
            return None

        result = self.analyze_reviews(
            product_title=product_info.get('title', 'Unknown Product'),
            product_description=product_info.get('description', 'No description'),
            reviews=reviews
        )

        if result:
            return result.get('analysis')
        return None
