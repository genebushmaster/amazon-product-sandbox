import os
import requests
import time
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class ApifyHandler:
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN environment variable is required")

        self.base_url = "https://api.apify.com/v2"
        # Amazon Reviews Scraper actor ID (using tilde separator for username~actor-name format)
        self.actor_id = "junglee~amazon-reviews-scraper"
        logger.info("Apify API handler initialized")

    def run_actor(self, input_data: Dict) -> Optional[str]:
        """
        Trigger Apify actor run with input data

        Args:
            input_data: Dictionary containing actor input parameters

        Returns:
            Run ID if successful, None otherwise
        """
        url = f"{self.base_url}/acts/{self.actor_id}/runs"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Running Apify actor: {self.actor_id}")
            logger.info(f"Input: {input_data}")
            response = requests.post(url, headers=headers, json=input_data)

            if response.status_code not in [200, 201]:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

            data = response.json()
            run_id = data.get("data", {}).get("id")

            if run_id:
                logger.info(f"Actor run started successfully. Run ID: {run_id}")
                return run_id
            else:
                logger.error(f"No run ID in response: {data}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def get_run_status(self, run_id: str) -> Dict:
        """
        Get status of actor run

        Args:
            run_id: Run ID from run_actor

        Returns:
            Run status data
        """
        url = f"{self.base_url}/actor-runs/{run_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return {}

            data = response.json()
            return data.get("data", {})

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}

    def wait_for_completion(self, run_id: str, max_wait: int = 1200, check_interval: int = 10) -> bool:
        """
        Poll for actor run completion

        Args:
            run_id: Run ID from run_actor
            max_wait: Maximum time to wait in seconds (default 1200 = 20 minutes)
            check_interval: Time between checks in seconds

        Returns:
            True if completed successfully, False otherwise
        """
        start_time = time.time()
        last_log_time = start_time
        logger.info(f"Waiting for actor run {run_id} to complete (max wait: {max_wait}s)")

        while (time.time() - start_time) < max_wait:
            status_data = self.get_run_status(run_id)

            if not status_data:
                logger.warning("Could not get run status")
                time.sleep(check_interval)
                continue

            status = status_data.get("status")

            # Log every 30 seconds instead of every 10 seconds
            current_time = time.time()
            should_log = (current_time - last_log_time) >= 30

            if should_log:
                elapsed = int(current_time - start_time)
                logger.info(f"Run status: {status} (elapsed: {elapsed}s)")
                last_log_time = current_time

            if status == "SUCCEEDED":
                logger.info("Actor run completed successfully")
                return True
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                logger.error(f"Actor run failed with status: {status}")
                return False
            elif status in ["RUNNING", "READY"]:
                time.sleep(check_interval)
            else:
                if should_log:
                    logger.info(f"Unknown status: {status}, waiting {check_interval}s...")
                time.sleep(check_interval)

        logger.warning(f"Timeout waiting for run {run_id}")
        return False

    def get_dataset_items(self, dataset_id: str) -> List[Dict]:
        """
        Retrieve items from dataset

        Args:
            dataset_id: Dataset ID from completed run

        Returns:
            List of dataset items
        """
        url = f"{self.base_url}/datasets/{dataset_id}/items"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }

        try:
            logger.info(f"Fetching dataset items from: {dataset_id}")
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return []

            items = response.json()
            logger.info(f"Retrieved {len(items)} items from dataset")
            return items

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def get_product_reviews(self, asin: str, amazon_domain: str = "amazon.com.au",
                           max_reviews: int = None) -> List[Dict]:
        """
        Fetch product reviews using Apify actor

        Args:
            asin: Amazon product ASIN
            amazon_domain: Amazon domain (default: amazon.com.au)
            max_reviews: Maximum number of reviews to fetch (optional)

        Returns:
            List of review dictionaries
        """
        # Construct product URL
        product_url = f"https://www.{amazon_domain}/dp/{asin}"

        # Prepare input for actor - productUrls expects array of objects with "url" field
        input_data = {
            "productUrls": [
                {"url": product_url}
            ],
            "maxReviews": max_reviews if max_reviews else 100,
            "filterByRatings": ["allStars"]
        }

        # Run actor
        run_id = self.run_actor(input_data)
        if not run_id:
            return []

        # Wait for completion
        if not self.wait_for_completion(run_id):
            return []

        # Get run details to find dataset ID
        run_data = self.get_run_status(run_id)
        dataset_id = run_data.get("defaultDatasetId")

        if not dataset_id:
            logger.error("No dataset ID found in run data")
            return []

        # Fetch results
        return self.get_dataset_items(dataset_id)
