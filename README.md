# Amazon Product Analysis Pipeline

An automated end-to-end pipeline that discovers Amazon products, collects reviews, analyzes them with AI, and generates professional HTML reports.

## Configuration

All settings are managed through `config.yaml`. Simply edit the file and run the scraper.

## Quick Start

1. Set up API keys in `.env`:
   ```bash
   SERP_API_KEY=your_key
   RAINFOREST_API_KEY=your_key
   APIFY_API_TOKEN=your_token
   GEMINI_API_KEY=your_key
   ```

2. Edit `config.yaml` with your search parameters

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the full pipeline:
   ```bash
   python3 pipeline.py
   ```

5. Results saved to timestamped folder in `data/`:
   ```
   data/YYYYMMDD-HHMMSS-query/
   ├── pipeline.log              # Complete execution log
   ├── serp_raw.json            # All SERP search results
   ├── serp_filtered.json       # Top 10 selected products
   ├── rainforest_products.json # Detailed product data
   ├── reviews.json             # All collected reviews
   ├── gemini_analysis.json     # AI analysis results
   └── report.html              # Final HTML report (auto-opens)
   ```

## Regenerate HTML Report

To regenerate just the HTML report from existing data (useful after tweaking the template):

```bash
# Use most recent run
python3 regenerate_html.py

# Or specify a run folder
python3 regenerate_html.py data/20251003-144207-magnetic-blocks-for-kids-100-p
```

## Important Notes

- **API Limits**: 250 total API calls per account. Each page = 1 API call.
- **Pagination**: Amazon typically returns ~48 products per page, with limits around 7-10 pages
- **Price Filters**: Use `p_36` parameter with price in cents (e.g., 3000 = $30)

## API Integrations

### SERP API (Product Search)
- **Purpose**: Search Amazon for products with complex filters
- **Handler**: `src/serp_handler.py`
- **Status**: Production ready
- **API Budget**: 250 requests total on free account

### Rainforest API (Product Data)
- **Purpose**: Fetch detailed product data and reviews
- **Handler**: `src/rainforest_handler.py`
- **Test Script**: `test_rainforest.py`
- **Status**: ⚠️ Product endpoint working, reviews endpoint temporarily unavailable (unlikely to become available)
- **Methods**:
  - `get_product_data(asin, amazon_domain)` - Fetch complete product data
  - `get_product_reviews(asin, amazon_domain, page)` - Fetch reviews by page (unavailable)
  - `get_all_reviews(asin, amazon_domain, max_pages)` - Fetch all reviews with pagination (unavailable)
- **Performance**: ~5 seconds per request
- **Output**: Includes title, ASIN, rating, ratings_total, price, main_image, feature_bullets, categories

### Apify API (Review Collection)
- **Purpose**: Fetch product reviews using Apify actors
- **Handler**: `src/apify_handler.py`
- **Test Script**: `test_apify.py`
- **Status**: Production ready
- **Actor**: `junglee~amazon-reviews-scraper`
- **Methods**:
  - `run_actor(input_data)` - Trigger actor with input configuration
  - `get_run_status(run_id)` - Check status of running actor
  - `wait_for_completion(run_id, max_wait)` - Poll until actor completes (max 10 min)
  - `get_dataset_items(dataset_id)` - Retrieve results from completed run
  - `get_product_reviews(asin, amazon_domain, max_reviews)` - Main method to fetch reviews
- **Performance**: ~13 seconds per run
- **Account Limitations**: Free tier returns 10 reviews per run
- **Output**: Includes reviewTitle, reviewDescription, ratingScore, date, isVerified, isAmazonVine

### BrightData API (Review Collection)
- **Purpose**: Fetch detailed product reviews via real-time browser scraping
- **Handler**: `src/brightdata_handler.py`
- **Test Script**: `test_brightdata.py`
- **Status**: Production ready
- **Dataset ID**: `gd_le8e811kzy4ggddlq`
- **Methods**:
  - `trigger_collection(amazon_url, limit_per_input, limit_multiple_results)` - Trigger collection
  - `get_snapshot_data(snapshot_id)` - Poll for snapshot data
  - `get_product_reviews(asin, amazon_url, domain, limit_multiple_results)` - Fetch reviews by ASIN or URL
- **Performance**: ~2-3 minutes per product (browser-based scraping with anti-bot evasion)
- **Account Limitations**: Preview mode returns 6-7 reviews per product (unverified account, unknown if this limit is lifted after verification)
- **Output**: Includes review_text, review_header, rating, author_name, is_verified, helpful_count

### Gemini API (Review Analysis)
- **Purpose**: Analyze product reviews to extract strengths and concerns using AI
- **Handler**: `src/gemini_handler.py`
- **Test Scripts**: `test_gemini.py` (full test), `test_prompt.py` (prompt preview)
- **Status**: Production ready
- **Model**: `gemini-2.5-flash`
- **Methods**:
  - `analyze_reviews(product_title, product_description, reviews)` - Analyze reviews and return strengths/concerns
  - `analyze_reviews_simple(reviews, product_info)` - Simplified version that extracts product info from reviews
- **Input Requirements**:
  - Product title and description (from Rainforest product data)
  - Reviews with ratingScore and reviewDescription fields (from Apify/Rainforest/BrightData)
- **Output Format**: Structured analysis with:
  - Product Strengths: 3-10 bullet points, ordered by frequency
  - Product Concerns: 3-10 bullet points, ordered by frequency
- **Performance**: ~23 seconds per analysis

## Testing Individual APIs

All API keys must be set in `.env` file first:
```bash
SERP_API_KEY=your_key
RAINFOREST_API_KEY=your_key
APIFY_API_TOKEN=your_token
BRIGHTDATA_API_KEY=your_key
GEMINI_API_KEY=your_key
```

### Test Rainforest API
```bash
python3 test_rainforest.py
# Output: data/reviews_rainforest_test.json
```

### Test Apify API
```bash
python3 test_apify.py
# Output: data/reviews_apify_test.json
```

### Test BrightData API
```bash
python3 test_brightdata.py
# Output: data/reviews_brightdata_test.json
```

### Test Gemini API
```bash
# Preview prompt without API call
python3 test_prompt.py

# Full test with API call - needs to be pointed to correct files
python3 test_gemini.py
# Output: data/reviews_analysis_gemini_test.json
```

## Pipeline Workflow

The automated pipeline (`pipeline.py`) performs the following steps:

1. **Product Discovery** (SERP API)
   - Searches Amazon with configured filters (domain, price, Prime shipping, etc.)
   - Applies client-side filtering (min rating, min reviews)
   - Selects top 10 products by: rating (desc) → review count (desc) → price (asc)
   - **Execution**: ~5 seconds for 2 pages
   - **Output**: `serp_raw.json`, `serp_filtered.json`

2. **Product Data Enrichment** (Rainforest API)
   - Fetches detailed product data for all 10 products in parallel
   - Extracts: title, feature_bullets, rating, ratings_total, price, main_image, categories
   - **Execution**: ~8 seconds (parallel)
   - **Output**: `rainforest_products.json`

3. **Review Collection** (Apify API)
   - Fetches 10 reviews per product sequentially (free tier limitation)
   - Reviews include: title, description, rating, verified status, date
   - **Execution**: ~4-5 minutes (10 products × ~30s each)
   - **Output**: `reviews.json` (100 reviews total)
   - **Note**: Configurable via `review_source` in `config.yaml`

4. **AI Analysis** (Gemini API)
   - Analyzes all 10 products in parallel using Gemini 2.5 Flash
   - Generates product strengths (3-10 points) and concerns (3-10 points)
   - Filters out duplicate/placeholder text automatically
   - Converts markdown formatting to HTML
   - **Execution**: ~40 seconds (parallel)
   - **Output**: `gemini_analysis.json`

5. **HTML Report Generation**
   - Generates professional single-page HTML report
   - Includes: product cards, images, pricing, ratings, AI analysis
   - Auto-opens in default browser
   - **Execution**: <1 second
   - **Output**: `report.html`

**Total Pipeline Time**: ~5-6 minutes for 10 products

## Performance & Cost

### API Usage per Run
- **SERP API**: 2 requests (configurable pages)
- **Rainforest API**: 10 requests (1 per product)
- **Apify API**: 10 actor runs (free tier: 10 reviews each)
- **Gemini API**: 10 analysis requests

### Optimization Features
- Intermediate saves after each step (no data loss on failure)
- Parallel execution where possible (Rainforest, Gemini)
- Sequential Apify execution (free tier constraint)
- Reduced logging verbosity (30s intervals for long-running tasks)
- 20-minute timeout for review collection