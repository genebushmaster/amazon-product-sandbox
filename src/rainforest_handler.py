import os
import requests
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class RainforestHandler:
    def __init__(self):
        self.api_key = os.getenv("RAINFOREST_API_KEY")
        if not self.api_key:
            raise ValueError("RAINFOREST_API_KEY environment variable is required")

        self.base_url = "https://api.rainforestapi.com/request"
        logger.info("Rainforest API handler initialized")

    def get_product_data(self, asin: str, amazon_domain: str = "amazon.com.au") -> Dict:
        """
        Fetch product data from Rainforest API

        Args:
            asin: Amazon product ASIN
            amazon_domain: Amazon domain (default: amazon.com.au)

        Returns:
            Complete API response dictionary with all product data
        """
        params = {
            "api_key": self.api_key,
            "asin": asin,
            "type": "product",
            "amazon_domain": amazon_domain
        }

        try:
            logger.info(f"Fetching product data for ASIN: {asin} from {amazon_domain}")
            response = requests.get(self.base_url, params=params)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return {}

            data = response.json()

            # Log sample of returned data structure
            if data:
                logger.info(f"Response keys: {list(data.keys())}")
                product = data.get("product", {})
                if product:
                    logger.info(f"Product title: {product.get('title', 'N/A')}")
                    logger.info(f"Product rating: {product.get('rating', 'N/A')}")

            return data

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}

    def get_product_reviews(self, asin: str, amazon_domain: str = "amazon.com.au",
                           page: int = 1) -> Dict:
        """
        Fetch product reviews from Rainforest API

        Args:
            asin: Amazon product ASIN
            amazon_domain: Amazon domain (default: amazon.com.au)
            page: Page number for pagination (default: 1)

        Returns:
            Complete API response dictionary with all review data
        """
        params = {
            "api_key": self.api_key,
            "asin": asin,
            "type": "reviews",
            "amazon_domain": amazon_domain,
            "page": page
        }

        try:
            logger.info(f"Fetching reviews for ASIN: {asin} from {amazon_domain} (page {page})")
            response = requests.get(self.base_url, params=params)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return {}

            data = response.json()

            # Log sample of returned data structure
            if data:
                logger.info(f"Response keys: {list(data.keys())}")
                reviews = data.get("reviews", [])
                logger.info(f"Retrieved {len(reviews)} reviews from page {page}")

                if reviews and len(reviews) > 0:
                    logger.info(f"Sample review keys: {list(reviews[0].keys())}")

            return data

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}

    def get_all_reviews(self, asin: str, amazon_domain: str = "amazon.com.au",
                       max_pages: int = None) -> List[Dict]:
        """
        Fetch all reviews across multiple pages

        Args:
            asin: Amazon product ASIN
            amazon_domain: Amazon domain (default: amazon.com.au)
            max_pages: Maximum number of pages to fetch (None = all available)

        Returns:
            List of all review dictionaries
        """
        all_reviews = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            data = self.get_product_reviews(asin, amazon_domain, page)

            if not data:
                logger.warning(f"No data returned for page {page}")
                break

            reviews = data.get("reviews", [])

            if not reviews:
                logger.info(f"No reviews found on page {page}, stopping pagination")
                break

            all_reviews.extend(reviews)

            # Check if there are more pages
            pagination = data.get("pagination", {})
            total_pages = pagination.get("total_pages", 1)

            logger.info(f"Page {page}/{total_pages} - collected {len(all_reviews)} total reviews so far")

            if page >= total_pages:
                logger.info(f"Reached last page ({total_pages})")
                break

            page += 1

        logger.info(f"Total reviews collected: {len(all_reviews)}")
        return all_reviews

    def get_reviews_with_metadata(self, asin: str, amazon_domain: str = "amazon.com.au",
                                  max_pages: int = None) -> Dict:
        """
        Fetch reviews and return complete response with metadata

        Args:
            asin: Amazon product ASIN
            amazon_domain: Amazon domain (default: amazon.com.au)
            max_pages: Maximum number of pages to fetch (None = all available)

        Returns:
            Dictionary containing reviews and product metadata
        """
        all_reviews = []
        page = 1
        product_data = None
        summary_data = None

        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            data = self.get_product_reviews(asin, amazon_domain, page)

            if not data:
                logger.warning(f"No data returned for page {page}")
                break

            # Capture product and summary data from first page
            if page == 1:
                product_data = data.get("product")
                summary_data = data.get("summary")

            reviews = data.get("reviews", [])

            if not reviews:
                logger.info(f"No reviews found on page {page}, stopping pagination")
                break

            all_reviews.extend(reviews)

            # Check if there are more pages
            pagination = data.get("pagination", {})
            total_pages = pagination.get("total_pages", 1)

            logger.info(f"Page {page}/{total_pages} - collected {len(all_reviews)} total reviews so far")

            if page >= total_pages:
                logger.info(f"Reached last page ({total_pages})")
                break

            page += 1

        result = {
            "asin": asin,
            "amazon_domain": amazon_domain,
            "product": product_data,
            "summary": summary_data,
            "total_reviews_collected": len(all_reviews),
            "reviews": all_reviews
        }

        logger.info(f"Complete data collected: {len(all_reviews)} reviews")
        return result
