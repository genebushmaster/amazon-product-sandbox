import os
import requests
import time
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv
try:
    from .models import Product
except ImportError:
    from models import Product

load_dotenv()

class AmazonScraper:
    def __init__(self):
        self.api_key = os.getenv("SERP_API_KEY")
        if not self.api_key:
            raise ValueError("SERP_API_KEY environment variable is required")

        self.base_url = "https://serpapi.com/search"
        logger.info("Amazon scraper initialized")

    def search_products(self, query: str, min_rating: float = None, min_price: float = None,
                       max_price: float = None, condition: str = "new", min_reviews: int = None,
                       limit: int = None) -> List[Dict]:
        params = {
            "engine": "amazon",
            "k": query,
            "amazon_domain": "amazon.com.au",
            "api_key": self.api_key
        }

        # Rating filter disabled for better client-side control
        # if min_rating and min_rating >= 4.0:
        #     params["p_72"] = "1248897011"  # 4+ stars

        # Add price filter for $50-$80 range
        if min_price and max_price:
            if min_price >= 50 and max_price <= 100:
                params["p_36"] = "1253506011"  # $50-$100 (closest range to $50-$80)
        elif max_price:
            # Fallback to original logic if only max_price is provided
            if max_price <= 25:
                params["p_36"] = "1253504011"  # Under $25
            elif max_price <= 50:
                params["p_36"] = "1253505011"  # $25-$50
            elif max_price <= 100:
                params["p_36"] = "1253506011"  # $50-$100

        # Add condition filter (default: new)
        if condition == "new":
            params["rh"] = "p_n_condition-type:New"

        try:
            logger.info(f"Searching Amazon with params: {params}")
            response = requests.get(self.base_url, params=params)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return []

            data = response.json()
            logger.info(f"API Response keys: {list(data.keys())}")

            products = data.get("products", [])
            if not products:
                # Try alternative keys
                products = data.get("organic_results", [])
                if not products:
                    logger.info(f"Raw response: {data}")
                    products = []

            logger.info(f"Raw products found before filtering: {len(products)}")

            # Review count filtering disabled - handled client-side
            # if min_reviews:
            #     products = [p for p in products
            #                if p.get("reviews", 0) >= min_reviews]

            # Post-filter by exact price range if both min_price and max_price specified
            if min_price and max_price:
                filtered_products = []
                for p in products:
                    price_str = p.get("price", "")
                    if price_str:
                        # Extract numeric price from string like "$59.99" or "59.99"
                        try:
                            price_num = float(price_str.replace("$", "").replace(",", ""))
                            if min_price <= price_num <= max_price:
                                filtered_products.append(p)
                        except (ValueError, AttributeError):
                            continue
                products = filtered_products

            # Limit disabled - return all results for client-side processing
            # if limit:
            #     products = products[:limit]

            logger.info(f"Found {len(products)} products for query: {query}")
            return products

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def search_products_paginated(self, query: str, amazon_domain: str = "amazon.com.au",
                                 language: str = None, shipping_location: str = None,
                                 pages: int = 5, prime_domestic: str = None, p_36: str = None,
                                 sort_param: str = None, delay: float = 1.0) -> List[Dict]:
        """
        Search products across multiple pages

        Args:
            query: Search query
            amazon_domain: Amazon domain (e.g., amazon.com.au)
            language: Language setting (e.g., amazon.com.au|en_AU)
            shipping_location: Shipping location filter (e.g., AU)
            pages: Number of pages to fetch (default 5)
            prime_domestic: Prime Domestic filter value (e.g., 6845356051)
            p_36: Price range filter (e.g., 3000-8000)
            sort_param: Sort parameter (e.g., review-rank)
            delay: Delay between requests in seconds

        Returns:
            Combined list of products from all pages
        """
        all_products = []

        for page_num in range(1, pages + 1):
            logger.info(f"Fetching page {page_num}/{pages}")

            # Base parameters
            params = {
                "engine": "amazon",
                "k": query,
                "amazon_domain": amazon_domain,
                "api_key": self.api_key,
                "page": page_num
            }

            # Add optional parameters
            if language:
                params["language"] = language
            if shipping_location:
                params["shipping_location"] = shipping_location
            if sort_param:
                params["s"] = sort_param

            # Build rh parameter
            rh_parts = []

            # Add Prime Domestic filter
            if prime_domestic:
                rh_parts.append(f"p_n_prime_domestic:{prime_domestic}")

            # Add price range filter
            if p_36:
                rh_parts.append(f"p_36:{p_36}")

            # Join all rh parts
            if rh_parts:
                params["rh"] = ",".join(rh_parts)

            try:
                logger.info(f"Searching page {page_num} with params: {params}")
                response = requests.get(self.base_url, params=params)

                if response.status_code != 200:
                    logger.error(f"API Error {response.status_code} on page {page_num}: {response.text}")
                    break

                data = response.json()

                # Extract products
                products = data.get("products", [])
                if not products:
                    products = data.get("organic_results", [])

                if not products:
                    logger.warning(f"No products found on page {page_num}")
                    break

                logger.info(f"Found {len(products)} products on page {page_num}")
                all_products.extend(products)

                # Check if there are more pages available
                pagination = data.get("serpapi_pagination", {})
                if not pagination.get("next"):
                    logger.info(f"No more pages available after page {page_num}")
                    break

                # Add delay between requests to be respectful
                if page_num < pages:
                    time.sleep(delay)

            except requests.RequestException as e:
                logger.error(f"Request failed on page {page_num}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page_num}: {e}")
                break

        logger.info(f"Total products collected across {pages} pages: {len(all_products)}")
        return all_products