from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from decimal import Decimal

class Product(BaseModel):
    title: str
    price: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    product_id: Optional[str] = None

class SearchResult(BaseModel):
    query: str
    location: str
    total_results: int
    products: List[Product]