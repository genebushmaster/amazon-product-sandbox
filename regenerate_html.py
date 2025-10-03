#!/usr/bin/env python3
import json
import yaml
from pathlib import Path
from src.report_generator import HTMLReportGenerator

def regenerate_html(run_folder: str):
    """Regenerate HTML report from existing data files"""

    run_path = Path(run_folder)

    if not run_path.exists():
        print(f"Error: Folder {run_folder} does not exist")
        return

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Load data files
    print(f"Loading data from {run_folder}...")

    with open(run_path / 'serp_filtered.json', 'r') as f:
        products = json.load(f)

    with open(run_path / 'rainforest_products.json', 'r') as f:
        product_data_list = json.load(f)

    with open(run_path / 'reviews.json', 'r') as f:
        all_reviews = json.load(f)

    with open(run_path / 'gemini_analysis.json', 'r') as f:
        analyses_with_context = json.load(f)

    # Restructure reviews into list of lists (per product)
    reviews_list = []
    for product in products:
        asin = product['asin']
        product_reviews = [r for r in all_reviews if r.get('asin') == asin]
        reviews_list.append(product_reviews)

    # Extract analyses (remove context wrapper)
    analyses = [item['analysis'] for item in analyses_with_context]

    # Generate HTML
    print("Generating HTML report...")
    generator = HTMLReportGenerator()
    html_path = run_path / 'report.html'

    generator.generate(
        config=config,
        products=products,
        product_data_list=product_data_list,
        reviews_list=reviews_list,
        analyses=analyses,
        output_path=html_path
    )

    print(f"HTML report generated: {html_path}")
    print(f"\nOpen with: file://{html_path.absolute()}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        run_folder = sys.argv[1]
    else:
        # Use most recent run folder
        data_path = Path('data')
        run_folders = sorted([d for d in data_path.iterdir() if d.is_dir()], reverse=True)
        if run_folders:
            run_folder = str(run_folders[0])
            print(f"Using most recent run: {run_folder}")
        else:
            print("No run folders found in data/")
            sys.exit(1)

    regenerate_html(run_folder)
