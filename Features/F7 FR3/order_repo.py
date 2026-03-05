"""Repository layer for order data – shared by Issues #38, #42, #61, #65.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class OrderRepo:
    """Handles persistence of order data to a JSON file."""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def load_all_orders(self) -> List[Dict[str, Any]]:
        """Load all orders from the JSON file.

        Creates an empty file if one does not already exist.
        """
        if not Path(self.data_path).is_file():
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Return a single order dict by ID, or None if not found."""
        orders = self.load_all_orders()
        for order in orders:
            if order["id"] == order_id:
                return order
        return None

    def save_order(self, order: Dict[str, Any]) -> None:
        """Append a new order to the JSON file."""
        orders = self.load_all_orders()
        orders.append(order)
        self._write(orders)

    def save_all_orders(self, orders: List[Dict[str, Any]]) -> None:
        """Overwrite all orders atomically using a temp file."""
        self._write(orders)

    def _write(self, orders: List[Dict[str, Any]]) -> None:
        """Write orders list to disk atomically."""
        temp_path = self.data_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.data_path)
      
