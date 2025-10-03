import os
import requests
import time
import json
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class BrightDataHandler:
    def __init__(self):
        self.api_key = os.getenv("BRIGHTDATA_API_KEY")
        if not self.api_key:
            raise ValueError("BRIGHTDATA_API_KEY environment variable is required")

        self.dataset_id = "gd_le8e811kzy4ggddlq"
        self.trigger_url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={self.dataset_id}&include_errors=true"
        self.snapshot_url = "https://api.brightdata.com/datasets/v3/snapshot"
        logger.info("BrightData API handler initialized")

    def trigger_collection(self, amazon_url: str, limit_per_input: int = 1000,
                          limit_multiple_results: int = None) -> Optional[str]:
        """
        Trigger BrightData collection for a product URL

        Args:
            amazon_url: Full Amazon product URL
            limit_per_input: Limit the number of results per input (default: 1000)
            limit_multiple_results: Limit the total number of results (optional)

        Returns:
            Snapshot ID if successful, None otherwise
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build trigger URL with pagination parameters
        trigger_url = f"{self.trigger_url}&limit_per_input={limit_per_input}"
        if limit_multiple_results:
            trigger_url += f"&limit_multiple_results={limit_multiple_results}"

        payload = [{"url": amazon_url}]

        try:
            logger.info(f"Triggering BrightData collection for URL: {amazon_url} (limit_per_input={limit_per_input}, limit_multiple_results={limit_multiple_results})")
            response = requests.post(trigger_url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

            data = response.json()
            snapshot_id = data.get("snapshot_id")

            if snapshot_id:
                logger.info(f"Collection triggered successfully. Snapshot ID: {snapshot_id}")
                return snapshot_id
            else:
                logger.error(f"No snapshot_id in response: {data}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def get_snapshot_data(self, snapshot_id: str, max_wait: int = 300, check_interval: int = 10) -> List[Dict]:
        """
        Poll for snapshot data until ready

        Args:
            snapshot_id: Snapshot ID from trigger_collection
            max_wait: Maximum time to wait in seconds (default 300 = 5 minutes)
            check_interval: Time between checks in seconds

        Returns:
            List of review dictionaries with text content
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        url = f"{self.snapshot_url}/{snapshot_id}"
        start_time = time.time()

        logger.info(f"Polling for snapshot {snapshot_id} (max wait: {max_wait}s)")

        while (time.time() - start_time) < max_wait:
            try:
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    # Parse NDJSON (newline-delimited JSON)
                    try:
                        # BrightData returns NDJSON, not regular JSON array
                        lines = response.text.strip().split('\n')
                        data = [json.loads(line) for line in lines if line.strip()]

                        if len(data) > 0:
                            logger.info(f"Snapshot ready! Retrieved {len(data)} records")
                            logger.debug(f"Total lines in response: {len(lines)}")
                            return self._parse_reviews(data)
                    except Exception as parse_error:
                        logger.error(f"Failed to parse response: {parse_error}")
                        logger.debug(f"Response text: {response.text[:500]}...")
                        return []

                elif response.status_code == 202:
                    logger.info(f"Snapshot not ready yet, waiting {check_interval}s...")
                    time.sleep(check_interval)
                    continue

                else:
                    logger.error(f"API Error {response.status_code}: {response.text}")
                    return []

            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return []

        logger.warning(f"Timeout waiting for snapshot {snapshot_id}")
        return []

    def _parse_reviews(self, data: List[Dict]) -> List[Dict]:
        """
        Parse BrightData response to extract review text

        Args:
            data: Raw BrightData response

        Returns:
            List of ALL review data (unfiltered)
        """
        reviews = []

        # Debug: log first record to see structure
        if data and len(data) > 0:
            logger.info(f"Sample record keys: {data[0].keys()}")
            logger.info(f"Full sample record: {json.dumps(data[0], indent=2)}")

        for record in data:
            # Save ALL data from BrightData, no filtering
            reviews.append(record)

        logger.info(f"Collected {len(reviews)} total records from BrightData")
        return reviews

    def get_product_reviews(self, asin: str = None, amazon_url: str = None,
                           domain: str = "amazon.com.au", limit_per_input: int = 1000,
                           limit_multiple_results: int = None) -> List[Dict]:
        """
        Fetch product reviews from BrightData API

        Args:
            asin: Amazon product ASIN (optional if amazon_url provided)
            amazon_url: Full Amazon product URL (optional if asin provided)
            domain: Amazon domain (default: amazon.com.au)
            limit_per_input: Limit the number of results per input (default: 1000)
            limit_multiple_results: Limit the total number of results (optional)

        Returns:
            List of review dictionaries with text content
        """
        # Build URL if not provided
        if not amazon_url:
            if not asin:
                logger.error("Either asin or amazon_url must be provided")
                return []
            amazon_url = f"https://{domain}/dp/{asin}/"

        # Trigger collection
        snapshot_id = self.trigger_collection(amazon_url, limit_per_input=limit_per_input,
                                             limit_multiple_results=limit_multiple_results)
        if not snapshot_id:
            return []

        # Wait for and retrieve results
        return self.get_snapshot_data(snapshot_id)

    def get_reviews_from_url(self, amazon_url: str, limit_per_input: int = 1000,
                            limit_multiple_results: int = None) -> List[Dict]:
        """
        Fetch reviews from Amazon URL

        Args:
            amazon_url: Full Amazon product URL
            limit_per_input: Limit the number of results per input (default: 1000)
            limit_multiple_results: Limit the total number of results (optional)

        Returns:
            List of review dictionaries with text content
        """
        return self.get_product_reviews(amazon_url=amazon_url, limit_per_input=limit_per_input,
                                       limit_multiple_results=limit_multiple_results)
