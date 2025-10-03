from typing import List, Dict
from datetime import datetime
from pathlib import Path


class HTMLReportGenerator:
    """Generate HTML reports for product analysis results"""

    def __init__(self):
        self.template = self._get_template()

    def _get_template(self) -> str:
        """Return HTML template with placeholders"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Product Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        header {{
            border-bottom: 3px solid #ff9900;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        h1 {{
            color: #232f3e;
            font-size: 2.5em;
            margin-bottom: 15px;
        }}

        .filter-params {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ff9900;
        }}

        .filter-params h2 {{
            font-size: 1.1em;
            color: #232f3e;
            margin-bottom: 10px;
        }}

        .filter-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}

        .filter-item {{
            font-size: 0.9em;
        }}

        .filter-label {{
            font-weight: 600;
            color: #555;
        }}

        .filter-value {{
            color: #000;
        }}

        .product-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 25px;
            padding: 20px;
            background-color: #fafafa;
        }}

        .product-header {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .product-image {{
            flex-shrink: 0;
        }}

        .product-image img {{
            width: 150px;
            height: 150px;
            object-fit: contain;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }}

        .product-info {{
            flex-grow: 1;
        }}

        .product-title {{
            font-size: 1.3em;
            color: #232f3e;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .product-title a {{
            color: #007185;
            text-decoration: none;
        }}

        .product-title a:hover {{
            color: #c45500;
            text-decoration: underline;
        }}

        .product-meta {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            font-size: 0.95em;
        }}

        .meta-label {{
            font-weight: 600;
            color: #555;
        }}

        .rating {{
            color: #ff9900;
            font-weight: 700;
        }}

        .price {{
            color: #b12704;
            font-weight: 700;
        }}

        .analysis {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}

        .analysis-column {{
            background-color: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}

        .strengths {{
            border-left: 4px solid #067d62;
        }}

        .concerns {{
            border-left: 4px solid #d13212;
        }}

        .analysis-column h3 {{
            margin-bottom: 10px;
            font-size: 1.05em;
        }}

        .strengths h3 {{
            color: #067d62;
        }}

        .concerns h3 {{
            color: #d13212;
        }}

        .analysis-column ul {{
            list-style: none;
            padding-left: 0;
        }}

        .analysis-column li {{
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
            font-size: 0.9em;
        }}

        .strengths li:before {{
            content: "+";
            position: absolute;
            left: 0;
            color: #067d62;
            font-weight: bold;
        }}

        .concerns li:before {{
            content: "-";
            position: absolute;
            left: 0;
            color: #d13212;
            font-weight: bold;
        }}

        @media (max-width: 768px) {{
            .product-header {{
                flex-direction: column;
            }}

            .analysis {{
                grid-template-columns: 1fr;
            }}

            .filter-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Query: {query}</h1>
            <div class="filter-params">
                <h2>Filter Parameters</h2>
                <div class="filter-grid">
                    <div class="filter-item">
                        <span class="filter-label">Domain:</span>
                        <span class="filter-value">{amazon_domain}</span>
                    </div>
                    <div class="filter-item">
                        <span class="filter-label">Shipping:</span>
                        <span class="filter-value">{shipping_type}</span>
                    </div>
                    <div class="filter-item">
                        <span class="filter-label">Price Range:</span>
                        <span class="filter-value">{price_range}</span>
                    </div>
                    <div class="filter-item">
                        <span class="filter-label">Min Rating:</span>
                        <span class="filter-value">{min_rating}</span>
                    </div>
                    <div class="filter-item">
                        <span class="filter-label">Min Reviews:</span>
                        <span class="filter-value">{min_reviews}</span>
                    </div>
                </div>
            </div>
        </header>

        <main>
            {product_cards}
        </main>
    </div>
</body>
</html>"""

    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown bold syntax to HTML"""
        import re
        # Convert **text** to <strong>text</strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        return text

    def _parse_analysis_text(self, analysis_text: str) -> tuple:
        """
        Parse Gemini analysis text into strengths and concerns lists

        Returns:
            Tuple of (strengths_list, concerns_list)
        """
        strengths = []
        concerns = []

        if not analysis_text:
            return strengths, concerns

        # Split into sections
        sections = analysis_text.split('**Product Concerns:**')

        if len(sections) >= 2:
            # Parse strengths
            strengths_text = sections[0].replace('**Product Strengths:**', '').strip()
            seen_strengths = set()
            for line in strengths_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets
                    cleaned = line.lstrip('0123456789.-) ').strip()
                    if cleaned:
                        # Convert markdown to HTML
                        html_text = self._markdown_to_html(cleaned)
                        # Deduplicate and filter out placeholder text
                        if html_text not in seen_strengths and not self._is_placeholder_text(html_text):
                            strengths.append(html_text)
                            seen_strengths.add(html_text)

            # Parse concerns
            concerns_text = sections[1].strip()
            seen_concerns = set()
            for line in concerns_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    cleaned = line.lstrip('0123456789.-) ').strip()
                    if cleaned:
                        # Convert markdown to HTML
                        html_text = self._markdown_to_html(cleaned)
                        # Deduplicate and filter out placeholder text
                        if html_text not in seen_concerns and not self._is_placeholder_text(html_text):
                            concerns.append(html_text)
                            seen_concerns.add(html_text)

        return strengths, concerns

    def _is_placeholder_text(self, text: str) -> bool:
        """Check if text is a placeholder/filler response from Gemini"""
        placeholder_patterns = [
            'no common concerns identified',
            'no concerns identified',
            'no specific concerns',
            'no major concerns',
            'no common strengths identified',
            'no strengths identified',
            'no specific strengths',
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in placeholder_patterns)

    def _generate_product_card(self, product: Dict, product_data: Dict,
                              reviews: List[Dict], analysis: Dict) -> str:
        """Generate HTML for a single product card"""

        # Extract product info
        title = product.get('title', 'Unknown Product')
        link = product.get('link_clean', product.get('link', '#'))
        thumbnail = product.get('thumbnail', '')
        rating = product.get('rating', 'N/A')
        review_count = product.get('reviews', 0)
        price = product.get('price', 'N/A')
        asin = product.get('asin', 'N/A')

        # Parse analysis
        analysis_text = analysis.get('analysis', '') if analysis else ''
        strengths, concerns = self._parse_analysis_text(analysis_text)

        strengths_html = "<ul>" + "".join(f"<li>{s}</li>" for s in strengths) + "</ul>" if strengths else "<p>No strengths identified</p>"
        concerns_html = "<ul>" + "".join(f"<li>{c}</li>" for c in concerns) + "</ul>" if concerns else "<p>No concerns identified</p>"

        # Build card HTML
        card = f"""
        <div class="product-card">
            <div class="product-header">
                <div class="product-image">
                    <img src="{thumbnail}" alt="{title}">
                </div>
                <div class="product-info">
                    <h2 class="product-title">
                        <a href="{link}" target="_blank">{title}</a>
                    </h2>
                    <div class="product-meta">
                        <div class="meta-item">
                            <span class="meta-label">ASIN:</span>
                            <span>{asin}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Rating:</span>
                            <span class="rating">{rating}/5</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Reviews:</span>
                            <span>{review_count:,}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Price:</span>
                            <span class="price">{price}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="analysis">
                <div class="analysis-column strengths">
                    <h3>Product Strengths</h3>
                    {strengths_html}
                </div>
                <div class="analysis-column concerns">
                    <h3>Product Concerns</h3>
                    {concerns_html}
                </div>
            </div>
        </div>
        """

        return card

    def generate(self, config: Dict, products: List[Dict], product_data_list: List[Dict],
                reviews_list: List[List[Dict]], analyses: List[Dict],
                output_path: Path) -> Path:
        """
        Generate complete HTML report

        Args:
            config: Configuration dictionary
            products: List of selected products
            product_data_list: List of Rainforest product data
            reviews_list: List of review lists
            analyses: List of Gemini analysis results
            output_path: Path where HTML file should be saved

        Returns:
            Path to generated HTML file
        """

        # Generate product cards
        product_cards_html = ""
        for i, product in enumerate(products):
            card = self._generate_product_card(
                product,
                product_data_list[i],
                reviews_list[i],
                analyses[i]
            )
            product_cards_html += card

        # Extract filter params
        refinements = config.get('refinements', {})
        client_filters = config.get('client_filters', {})

        # Determine shipping type
        p_n_prime = refinements.get('p_n_prime_domestic')
        if p_n_prime == '6845356051':
            shipping_type = 'Prime Domestic'
        elif p_n_prime == '6845357051':
            shipping_type = 'Prime International'
        elif p_n_prime:
            shipping_type = f'Prime ({p_n_prime})'
        else:
            shipping_type = 'Any'

        # Format price range
        p_36 = refinements.get('p_36')
        if p_36:
            try:
                min_p, max_p = p_36.split('-')
                price_range = f'${int(min_p)/100:.2f} - ${int(max_p)/100:.2f}'
            except:
                price_range = p_36
        else:
            price_range = 'Any'

        # Fill template
        html = self.template.format(
            query=config.get('query', 'N/A'),
            amazon_domain=config.get('amazon_domain', 'N/A'),
            shipping_type=shipping_type,
            price_range=price_range,
            min_rating=client_filters.get('min_rating', 'Any'),
            min_reviews=client_filters.get('min_reviews', 'Any'),
            product_cards=product_cards_html
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path
