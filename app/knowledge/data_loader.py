"""
Dataset loader for VocalChaos synthetic e-commerce database.
Loads company policies, products, customers, orders, and shipment tracking records into memory.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("vocalchaos.data_loader")

DATA_DIR = Path(__file__).parent / "data"

class DataLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not getattr(self, "_loaded", False):
            self.policies: Dict[str, Any] = {}
            self.products: List[Dict[str, Any]] = []
            self.customers: List[Dict[str, Any]] = []
            self.orders: List[Dict[str, Any]] = []
            self.shipments: List[Dict[str, Any]] = []
            self.load_data()
            self._loaded = True

    def load_data(self):
        """Load JSON datasets from app/knowledge/data/ directory."""
        try:
            policies_file = DATA_DIR / "company_policies.json"
            if policies_file.exists():
                with open(policies_file, "r", encoding="utf-8") as f:
                    self.policies = json.load(f)

            products_file = DATA_DIR / "products.json"
            if products_file.exists():
                with open(products_file, "r", encoding="utf-8") as f:
                    self.products = json.load(f)

            customers_file = DATA_DIR / "customers.json"
            if customers_file.exists():
                with open(customers_file, "r", encoding="utf-8") as f:
                    self.customers = json.load(f)

            orders_file = DATA_DIR / "orders.json"
            if orders_file.exists():
                with open(orders_file, "r", encoding="utf-8") as f:
                    self.orders = json.load(f)

            shipments_file = DATA_DIR / "shipments.json"
            if shipments_file.exists():
                with open(shipments_file, "r", encoding="utf-8") as f:
                    self.shipments = json.load(f)

            logger.info(
                f"Successfully loaded dataset: {len(self.products)} products, "
                f"{len(self.customers)} customers, {len(self.orders)} orders, "
                f"{len(self.shipments)} shipments."
            )
        except Exception as e:
            logger.error(f"Error loading synthetic dataset: {str(e)}")

# Singleton helper instance
data_loader = DataLoader()
