#!/usr/bin/env python3
import os
import sys
import yaml
import asyncio
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger

try:
    from src.serp_handler import AmazonScraper
    from src.rainforest_handler import RainforestHandler
    from src.apify_handler import ApifyHandler
    from src.gemini_handler import GeminiHandler
    from src.report_generator import HTMLReportGenerator
    from src.utils import save_to_json
except ImportError:
    from serp_handler import AmazonScraper
    from rainforest_handler import RainforestHandler
    from apify_handler import ApifyHandler
    from gemini_handler import GeminiHandler
    from report_generator import HTMLReportGenerator
    from utils import save_to_json


class ProductAnalysisPipeline:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.run_folder = None
        self.log_file_path = None

    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config

    def create_run_folder(self) -> Path:
        """Create timestamped folder for this pipeline run"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        query = self.config['query']

        # Sanitize query for folder name (remove special chars, limit length)
        query_clean = "".join(c if c.isalnum() or c.isspace() else '' for c in query)
        query_clean = "-".join(query_clean.split())[:30]

        folder_name = f"{timestamp}-{query_clean}"
        run_folder = Path("data") / folder_name
        run_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created run folder: {run_folder}")
        return run_folder

    def setup_logging(self):
        """Configure logging to console and file"""
        # Remove default logger
        logger.remove()

        # Add console logger (INFO level, clean messages)
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
            colorize=True
        )

        # Add file logger (DEBUG level, verbose)
        self.log_file_path = self.run_folder / "pipeline.log"
        logger.add(
            self.log_file_path,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="10 MB"
        )

        logger.info(f"Logging to: {self.log_file_path}")

    def select_top_products(self, products: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Select top N products by rating (desc), review count (desc), price (asc)

        Args:
            products: List of product dictionaries
            limit: Number of products to select (default 10)

        Returns:
            List of top N products
        """
        logger.info(f"Selecting top {limit} products from {len(products)} candidates")

        # Sort by rating (desc), then reviews (desc), then price (asc)
        def sort_key(p):
            rating = p.get('rating', 0) or 0
            reviews = p.get('reviews', 0) or 0

            # Handle price - extract numeric value if it's a string
            price = p.get('price', 0)
            if isinstance(price, str):
                # Remove currency symbols and convert to float
                price_clean = ''.join(c for c in price if c.isdigit() or c == '.')
                price = float(price_clean) if price_clean else 999999
            elif price is None:
                price = 999999

            return (-rating, -reviews, price)

        sorted_products = sorted(products, key=sort_key)
        top_products = sorted_products[:limit]

        logger.info(f"Selected {len(top_products)} products:")
        for i, product in enumerate(top_products, 1):
            logger.info(f"  {i}. {product['title'][:50]}... - Rating: {product.get('rating', 'N/A')}, Reviews: {product.get('reviews', 0)}, Price: {product.get('price', 'N/A')}")

        return top_products

    async def fetch_product_data_async(self, handler: RainforestHandler, asin: str,
                                      domain: str) -> Dict:
        """Async wrapper for Rainforest product data fetch"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler.get_product_data, asin, domain)

    async def fetch_reviews_async(self, handler: ApifyHandler, asin: str,
                                 domain: str) -> List[Dict]:
        """Async wrapper for Apify reviews fetch"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler.get_product_reviews, asin, domain, None)

    async def analyze_with_gemini_async(self, handler: GeminiHandler, product_title: str,
                                       product_description: str, reviews: List[Dict]) -> Dict:
        """Async wrapper for Gemini analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler.analyze_reviews,
                                         product_title, product_description, reviews)

    async def collect_product_data(self, products: List[Dict]) -> tuple:
        """
        Collect product data and reviews for all products
        Rainforest runs in parallel, Apify runs sequentially

        Args:
            products: List of product dictionaries with ASINs

        Returns:
            Tuple of (product_data_list, reviews_list)
        """
        amazon_domain = self.config['amazon_domain']
        rainforest = RainforestHandler()
        apify = ApifyHandler()

        logger.info(f"Fetching product data and reviews for {len(products)} products...")

        # Create tasks for Rainforest (parallel is fine)
        product_tasks = []
        for product in products:
            asin = product['asin']
            product_tasks.append(self.fetch_product_data_async(rainforest, asin, amazon_domain))

        # Execute Rainforest tasks in parallel
        logger.info("Running Rainforest API calls in parallel...")
        product_data_results = await asyncio.gather(*product_tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(product_data_results):
            if isinstance(result, Exception):
                logger.error(f"Product data fetch failed for ASIN {products[i]['asin']}: {result}")
                raise result

        # Run Apify sequentially (free tier can't handle parallel)
        logger.info("Running Apify API calls sequentially...")
        review_results = []
        for i, product in enumerate(products):
            asin = product['asin']
            logger.info(f"Fetching reviews for product {i+1}/{len(products)}: {asin}")
            try:
                reviews = await self.fetch_reviews_async(apify, asin, amazon_domain)
                review_results.append(reviews)
                logger.info(f"Retrieved {len(reviews)} reviews for {asin}")
            except Exception as e:
                logger.error(f"Reviews fetch failed for ASIN {asin}: {e}")
                raise e

        logger.info("All product data and reviews fetched successfully")
        return product_data_results, review_results

    async def analyze_all_products(self, products: List[Dict], product_data_list: List[Dict],
                                  reviews_list: List[List[Dict]]) -> List[Dict]:
        """
        Analyze all products with Gemini in parallel

        Args:
            products: List of original product dictionaries
            product_data_list: List of Rainforest product data
            reviews_list: List of review lists

        Returns:
            List of analysis results
        """
        gemini = GeminiHandler()

        logger.info(f"Analyzing {len(products)} products with Gemini AI...")

        # Create analysis tasks
        analysis_tasks = []
        for i, product in enumerate(products):
            # Extract product info from Rainforest data
            rf_product = product_data_list[i].get('product', {})
            title = rf_product.get('title', product.get('title', 'Unknown Product'))

            # Build description from feature bullets
            feature_bullets = rf_product.get('feature_bullets', [])
            if isinstance(feature_bullets, list):
                description = "\n".join(f"- {bullet}" for bullet in feature_bullets)
            else:
                description = str(feature_bullets) if feature_bullets else "No description available"

            reviews = reviews_list[i]

            analysis_tasks.append(
                self.analyze_with_gemini_async(gemini, title, description, reviews)
            )

        # Execute all analysis tasks in parallel
        logger.info("Running Gemini analysis in parallel...")
        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(analysis_results):
            if isinstance(result, Exception):
                logger.error(f"Gemini analysis failed for product {i+1}: {result}")
                raise result

        logger.info("All analyses completed successfully")
        return analysis_results

    def save_results(self, serp_raw: List[Dict], serp_filtered: List[Dict],
                    product_data: List[Dict], reviews: List[List[Dict]],
                    analyses: List[Dict]):
        """Save all results to JSON files"""
        logger.info("Saving results to files...")

        # Save SERP results
        save_to_json(serp_raw, "serp_raw.json", output_dir=str(self.run_folder))
        logger.info(f"Saved SERP raw results: {len(serp_raw)} products")

        save_to_json(serp_filtered, "serp_filtered.json", output_dir=str(self.run_folder))
        logger.info(f"Saved SERP filtered results: {len(serp_filtered)} products")

        # Save Rainforest product data
        save_to_json(product_data, "rainforest_products.json", output_dir=str(self.run_folder))
        logger.info(f"Saved Rainforest product data: {len(product_data)} products")

        # Save reviews (combine all reviews with product context)
        all_reviews = []
        for i, review_list in enumerate(reviews):
            for review in review_list:
                review['asin'] = serp_filtered[i]['asin']
                review['product_title'] = serp_filtered[i]['title']
                all_reviews.append(review)

        save_to_json(all_reviews, "reviews.json", output_dir=str(self.run_folder))
        logger.info(f"Saved reviews: {len(all_reviews)} total reviews")

        # Save Gemini analyses
        analyses_with_context = []
        for i, analysis in enumerate(analyses):
            analyses_with_context.append({
                'asin': serp_filtered[i]['asin'],
                'product_title': serp_filtered[i]['title'],
                'analysis': analysis
            })

        save_to_json(analyses_with_context, "gemini_analysis.json", output_dir=str(self.run_folder))
        logger.info(f"Saved Gemini analyses: {len(analyses_with_context)} products")

        logger.info("All results saved successfully")

    def generate_html_report(self, products: List[Dict], product_data: List[Dict],
                           reviews: List[List[Dict]], analyses: List[Dict]) -> Path:
        """
        Generate HTML report

        Returns:
            Path to generated HTML file
        """
        logger.info("Generating HTML report...")

        html_path = self.run_folder / "report.html"
        generator = HTMLReportGenerator()

        generator.generate(
            config=self.config,
            products=products,
            product_data_list=product_data,
            reviews_list=reviews,
            analyses=analyses,
            output_path=html_path
        )

        logger.info(f"HTML report generated: {html_path}")
        return html_path

    def launch_browser(self, html_path: Path):
        """Open HTML report in default browser"""
        logger.info("Launching browser...")
        webbrowser.open(f"file://{html_path.absolute()}")
        logger.info("Browser launched")

    async def run(self):
        """Execute full pipeline"""
        try:
            # Step 1: Setup
            logger.info("=" * 60)
            logger.info("Starting Product Analysis Pipeline")
            logger.info("=" * 60)

            self.run_folder = self.create_run_folder()
            self.setup_logging()

            query = self.config['query']
            logger.info(f"Query: {query}")
            logger.info(f"Domain: {self.config['amazon_domain']}")

            # Step 2: SERP Search
            logger.info("Running SERP search...")
            scraper = AmazonScraper()

            raw_results = scraper.search_products_paginated(
                query=query,
                amazon_domain=self.config['amazon_domain'],
                language=self.config['language'],
                shipping_location=self.config['shipping_location'],
                pages=self.config['pages'],
                prime_domestic=self.config.get('refinements', {}).get('p_n_prime_domestic'),
                p_36=self.config.get('refinements', {}).get('p_36'),
                sort_param=self.config.get('sort'),
                delay=self.config['delay']
            )

            if not raw_results:
                logger.error("No products found from SERP search")
                return

            logger.info(f"SERP search completed: {len(raw_results)} products found")

            # Save raw SERP results immediately
            save_to_json(raw_results, "serp_raw.json", output_dir=str(self.run_folder))
            logger.info(f"Saved SERP raw results: {len(raw_results)} products")

            # Step 3: Filter and select top products
            logger.info("Filtering products...")

            # Apply client-side filters
            filtered_products = []
            seen_asins = set()

            client_filters = self.config.get('client_filters', {})
            min_rating = client_filters.get('min_rating')
            min_reviews = client_filters.get('min_reviews')

            for product in raw_results:
                asin = product.get("asin")
                if asin in seen_asins:
                    continue

                rating = product.get("rating")
                reviews = product.get("reviews", 0)

                passes_rating = min_rating is None or (rating and rating >= min_rating)
                passes_reviews = min_reviews is None or (reviews and reviews >= min_reviews)

                if passes_rating and passes_reviews:
                    filtered_product = {
                        "asin": asin,
                        "title": product.get("title"),
                        "link": product.get("link"),
                        "link_clean": product.get("link_clean"),
                        "thumbnail": product.get("thumbnail"),
                        "rating": product.get("rating"),
                        "reviews": product.get("reviews"),
                        "price": product.get("price")
                    }
                    filtered_products.append(filtered_product)
                    seen_asins.add(asin)

            logger.info(f"Filtering completed: {len(filtered_products)} products passed filters")

            if not filtered_products:
                logger.error("No products passed filters")
                return

            # Select top 10
            top_products = self.select_top_products(filtered_products, limit=10)

            # Save filtered results immediately
            save_to_json(top_products, "serp_filtered.json", output_dir=str(self.run_folder))
            logger.info(f"Saved top 10 filtered products")

            # Step 4: Collect product data and reviews
            product_data_list, reviews_list = await self.collect_product_data(top_products)

            # Save Rainforest product data immediately
            save_to_json(product_data_list, "rainforest_products.json", output_dir=str(self.run_folder))
            logger.info(f"Saved Rainforest product data: {len(product_data_list)} products")

            # Save reviews immediately
            all_reviews = []
            for i, review_list in enumerate(reviews_list):
                for review in review_list:
                    review['asin'] = top_products[i]['asin']
                    review['product_title'] = top_products[i]['title']
                    all_reviews.append(review)
            save_to_json(all_reviews, "reviews.json", output_dir=str(self.run_folder))
            logger.info(f"Saved reviews: {len(all_reviews)} total reviews")

            # Step 5: Analyze with Gemini in parallel
            analyses = await self.analyze_all_products(top_products, product_data_list, reviews_list)

            # Save Gemini analyses immediately
            analyses_with_context = []
            for i, analysis in enumerate(analyses):
                analyses_with_context.append({
                    'asin': top_products[i]['asin'],
                    'product_title': top_products[i]['title'],
                    'analysis': analysis
                })
            save_to_json(analyses_with_context, "gemini_analysis.json", output_dir=str(self.run_folder))
            logger.info(f"Saved Gemini analyses: {len(analyses_with_context)} products")

            # Step 6: Save all results
            self.save_results(raw_results, top_products, product_data_list, reviews_list, analyses)

            # Step 7: Generate HTML report
            html_path = self.generate_html_report(top_products, product_data_list, reviews_list, analyses)

            # Step 8: Launch browser
            self.launch_browser(html_path)

            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Results saved to: {self.run_folder}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            logger.exception(e)
            raise


def main():
    """Entry point for pipeline"""
    pipeline = ProductAnalysisPipeline()
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
