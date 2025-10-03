# Claude Code Preferences - Amazon Sandbox

## Project Overview
Automated end-to-end pipeline that discovers Amazon products via SERP API, enriches with Rainforest product data, collects reviews via Apify, analyzes with Gemini AI, and generates professional HTML reports. Fully operational and production-ready.

## Project Status
- **Core functionality**: ✅ Complete automated pipeline (pipeline.py)
- **Product discovery**: ✅ SERP API with smart filtering and top-10 selection
- **Product data**: ✅ Rainforest API product endpoint (parallel execution)
- **Review collection**: ✅ Apify API (10 reviews/product, sequential execution)
- **AI analysis**: ✅ Gemini 2.5 Flash (parallel analysis, markdown→HTML conversion)
- **HTML reports**: ✅ Professional single-page reports with auto-launch
- **Data persistence**: ✅ Timestamped folders with intermediate saves

## Tech Stack
- **Language**: Python 3.10+
- **Async**: asyncio for parallel API execution
- **HTTP Client**: requests
- **Data Models**: Pydantic (for structured product data)
- **Configuration**: PyYAML
- **Logging**: loguru (dual output: console + file)
- **Data Export**: JSON (structured intermediate saves)
- **HTML Generation**: Custom template-based generator with CSS
- **Environment**: python-dotenv for API key management

## Key Implementation Learnings

### SERP API
1. **Amazon engine requires `k` parameter** (not `q`)
2. **Response data in `organic_results`** (not `products`)
3. **Price filters use p_36 with cents** - e.g., 3000-8000 = $30-$80
4. **Prime Domestic filter** - Requires p_n_prime_domestic in rh parameter
5. **Review count filtering** - Done client-side post-API
6. **Sort parameters affect results** - Different sorting can return different product counts
7. **ASIN deduplication** - Must be done client-side (pipeline.py)

### Pipeline Optimization
1. **Apify free tier** - Must run sequentially (10 parallel actors timeout after 10min)
2. **Rainforest & Gemini** - Can run in parallel (no rate limit issues)
3. **Intermediate saves** - Critical for long pipelines (prevent data loss on timeout)
4. **Logging verbosity** - Reduce to 30s intervals for long-running tasks (Apify)
5. **Product selection** - Sort by rating→reviews→price for best results
6. **Gemini markdown** - Must convert **bold** to <strong> for HTML rendering
7. **Placeholder filtering** - Remove duplicate "no concerns identified" responses

## API Integration Quick Reference
- **SERP API**: Product search (`serp_handler.py`) - ~2-3s for 2 pages
- **Rainforest API**: Product data (`rainforest_handler.py`) - ~8s for 10 products (parallel)
- **Apify API**: Review collection (`apify_handler.py`) - ~4-5min for 10 products (sequential, 10 reviews each)
- **BrightData API**: Review collection (`brightdata_handler.py`) - 6-7 reviews in preview mode (not currently used)
- **Gemini API**: AI review analysis (`gemini_handler.py`) - ~40s for 10 products (parallel)
- **Report Generator**: HTML generation (`report_generator.py`) - <1s with markdown conversion

See README.md for detailed API documentation and test scripts.

## Code Style & Preferences
- **Imports**: Use try/except for relative imports pattern
- **Error Handling**: Comprehensive logging with loguru
- **Data Models**: Pydantic for validation and structure
- **Configuration**: YAML for all settings (config.yaml)
- **API responses**: Return complete unfiltered data, let client decide what to use
- **Naming**: Descriptive function names, clear parameter names

## Development Notes
- **Main Entry Point**: `pipeline.py` (full automated workflow)
- **HTML Regeneration**: `regenerate_html.py` (rebuild report without re-running pipeline)
- **API Budget Management**: Track usage carefully (SERP API: 250 total requests = ~125 pipeline runs)
- **Configuration**: All settings in config.yaml (no CLI needed)
- **Testing**: Individual test scripts for each API (test_*.py)
- **Output Structure**: Timestamped folders in data/ (e.g., `data/20251003-144207-magnetic-blocks-for-kids-100-p/`)
- **Logging**: Dual output - console (INFO, clean) + file (DEBUG, verbose)
- **Data Persistence**: Intermediate saves after each pipeline step (SERP, Rainforest, Apify, Gemini)
- **Account Limitations**:
  - Apify free tier: 10 reviews per product (must run sequentially)
  - BrightData preview: 6-7 reviews per product
  - Rainforest reviews endpoint: Temporarily unavailable
  - Gemini free tier: Generous limits (sufficient for development)

## Files Generated Per Run
```
data/YYYYMMDD-HHMMSS-query/
├── pipeline.log              # Complete execution log
├── serp_raw.json            # All SERP results (before filtering)
├── serp_filtered.json       # Top 10 selected products
├── rainforest_products.json # Detailed product data
├── reviews.json             # All reviews (100 total)
├── gemini_analysis.json     # AI analysis results
└── report.html              # Final HTML report
```
