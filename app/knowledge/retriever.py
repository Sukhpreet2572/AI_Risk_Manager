"""
Entity Extraction & Data Retrieval Layer for VocalChaos.
Retrieves grounded company database records (orders, products, customers, shipments, policies)
matching extracted entities from customer queries and conversation memory.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Set

from app.knowledge.data_loader import data_loader

logger = logging.getLogger("vocalchaos.retriever")


def get_customer(customer_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve customer profile by customer_id or full/first name."""
    if not customer_identifier:
        return None
    clean_id = customer_identifier.strip().upper()
    for cust in data_loader.customers:
        if cust["customer_id"].upper() == clean_id:
            return cust
        if clean_id in cust["name"].upper():
            return cust
    return None


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve order details by order_id (e.g. 'ORD-2400321' or '2400321')."""
    if not order_id:
        return None
    clean_id = str(order_id).strip().upper()
    if not clean_id.startswith("ORD-") and clean_id.isdigit():
        clean_id = f"ORD-{clean_id}"

    for order in data_loader.orders:
        if order["order_id"].upper() == clean_id:
            return order
    return None


def get_product(product_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieve product details by product_id or product_name search."""
    if not product_identifier:
        return None
    clean_id = str(product_identifier).strip().upper()
    for prod in data_loader.products:
        if prod["product_id"].upper() == clean_id or clean_id in prod["product_name"].upper():
            return prod
    return None


def get_shipment(tracking_or_order_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve shipment tracking information by tracking_number or order_id."""
    if not tracking_or_order_id:
        return None
    clean_id = str(tracking_or_order_id).strip().upper()
    if not clean_id.startswith("TRK-") and clean_id.isdigit() and len(clean_id) == 5:
        clean_id = f"TRK-{clean_id}"
    if not clean_id.startswith("ORD-") and clean_id.isdigit() and len(clean_id) == 7:
        clean_id = f"ORD-{clean_id}"

    for ship in data_loader.shipments:
        if ship["tracking_number"].upper() == clean_id or ship["order_id"].upper() == clean_id:
            return ship
    return None


def search_orders_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Get all orders belonging to a specific customer ID."""
    if not customer_id:
        return []
    clean_id = customer_id.strip().upper()
    return [o for o in data_loader.orders if o["customer_id"].upper() == clean_id]


def search_products(query: str) -> List[Dict[str, Any]]:
    """Search products matching text query."""
    if not query:
        return []
    q = query.lower()
    return [
        p for p in data_loader.products
        if q in p["product_name"].lower() or q in p["category"].lower() or q in p["description"].lower()
    ]


def get_relevant_policies(query: str) -> Dict[str, Any]:
    """Retrieve policies relevant to query keywords."""
    policies = data_loader.policies
    if not query:
        return policies
    q = query.lower()
    matched = {}
    for key, pol in policies.items():
        title = pol.get("title", "").lower()
        rules_text = " ".join(pol.get("rules", [])).lower()
        if any(w in title or w in rules_text for w in q.split()):
            matched[key] = pol
    return matched if matched else policies


def extract_entities(text: str, active_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract order_id, tracking_number, customer_id, product_id, and names from text,
    falling back to persistent conversation state if present.
    """
    entities = {
        "order_id": None,
        "tracking_number": None,
        "customer_id": None,
        "product_id": None,
        "customer_name": None,
        "product_query": None,
        "is_non_existent_order": False
    }

    state = active_state or {}

    # Extract Order ID (e.g. ORD-2400321, 2400321, 12345, 9999999)
    order_match = re.search(r"\b(ORD-\d{7}|\d{7}|\d{5})\b", text, re.IGNORECASE)
    if order_match:
        raw_order = order_match.group(1).upper()
        if not raw_order.startswith("ORD-") and len(raw_order) == 7:
            raw_order = f"ORD-{raw_order}"
        entities["order_id"] = raw_order
    elif state.get("order_id"):
        entities["order_id"] = state.get("order_id")

    # Extract Tracking Number (e.g. TRK-88202, TRK-99999, ABC999)
    tracking_match = re.search(r"\b(TRK-\d{5}|\b[A-Z]{3}\d{3}\b)\b", text, re.IGNORECASE)
    if tracking_match:
        entities["tracking_number"] = tracking_match.group(1).upper()
    elif state.get("tracking_number"):
        entities["tracking_number"] = state.get("tracking_number")

    # Extract Customer Name
    for cust in data_loader.customers:
        first_name = cust["name"].split()[0]
        if first_name.lower() in text.lower() or cust["name"].lower() in text.lower():
            entities["customer_name"] = cust["name"]
            entities["customer_id"] = cust["customer_id"]
            break

    if not entities["customer_id"] and state.get("customer_id"):
        entities["customer_id"] = state.get("customer_id")
        entities["customer_name"] = state.get("customer_name")

    # Check if order_id exists in database
    if entities["order_id"]:
        order_record = get_order(entities["order_id"])
        if not order_record and ("ORD-" in entities["order_id"] or len(entities["order_id"]) == 7 or entities["order_id"] == "12345"):
            entities["is_non_existent_order"] = True

    return entities


def compile_grounded_context(entities: Dict[str, Any]) -> str:
    """
    Retrieves and formats ground-truth records matching extracted entities into a clear, structured block.
    """
    sections = []

    order_id = entities.get("order_id")
    tracking_number = entities.get("tracking_number")
    customer_id = entities.get("customer_id")

    # 1. Order Ground Truth
    if order_id:
        order = get_order(order_id)
        if order:
            sections.append(
                f"[VERIFIED GROUND TRUTH — ORDER RECORD FOR {order['order_id']}]\n"
                f"- Order ID: {order['order_id']}\n"
                f"- Customer Name: {order['customer_name']} (Customer ID: {order['customer_id']})\n"
                f"- Product: {order['product_name']} (Product ID: {order['product_id']})\n"
                f"- Order Date: {order['order_date']}\n"
                f"- Total Price: ${order['total_price']}\n"
                f"- Payment Status: {order['payment_status']}\n"
                f"- Order Status: {order['order_status']}\n"
                f"- Shipment Status: {order['shipment_status']}\n"
                f"- Tracking Number: {order['tracking_number'] or 'None Assigned'}\n"
                f"- Estimated Delivery: {order['estimated_delivery'] or 'N/A'}\n"
                f"- Actual Delivery Date: {order['delivery_date'] or 'Not Delivered'}\n"
                f"- Return Eligible: {order['return_eligible']}\n"
                f"- Refund Status: {order['refund_status']}\n"
                f"- Manager Approval: {order['manager_approval'] or 'None (No manager approval exists)'}\n"
                f"- Internal System Notes: {order['notes']}"
            )
            # Fetch shipment details if order exists
            shipment = get_shipment(order['order_id'])
            if shipment:
                sections.append(
                    f"[VERIFIED GROUND TRUTH — SHIPMENT RECORD FOR {order['order_id']}]\n"
                    f"- Carrier: {shipment['carrier']}\n"
                    f"- Shipment Status: {shipment['shipment_status']}\n"
                    f"- Shipped Date: {shipment['shipped_date'] or 'N/A'}\n"
                    f"- Estimated Delivery: {shipment['estimated_delivery'] or 'N/A'}\n"
                    f"- Actual Delivery: {shipment['actual_delivery'] or 'N/A'}"
                )
        else:
            sections.append(
                f"[VERIFIED GROUND TRUTH — ORDER RECORD FOR {order_id}]\n"
                f"⚠️ ORDER '{order_id}' DOES NOT EXIST IN THE COMPANY DATABASE. IT IS NON-EXISTENT."
            )

    # 2. Tracking Number lookup if provided separately
    if tracking_number and not order_id:
        shipment = get_shipment(tracking_number)
        if shipment:
            sections.append(
                f"[VERIFIED GROUND TRUTH — TRACKING RECORD FOR {tracking_number}]\n"
                f"- Tracking Number: {shipment['tracking_number']}\n"
                f"- Order ID: {shipment['order_id']}\n"
                f"- Carrier: {shipment['carrier']}\n"
                f"- Status: {shipment['shipment_status']}\n"
                f"- Estimated Delivery: {shipment['estimated_delivery']}"
            )
        else:
            sections.append(
                f"[VERIFIED GROUND TRUTH — TRACKING RECORD FOR {tracking_number}]\n"
                f"⚠️ TRACKING NUMBER '{tracking_number}' DOES NOT EXIST IN THE COURIER LOGISTICS DATABASE."
            )

    # 3. Customer Profile Ground Truth
    if customer_id:
        cust = get_customer(customer_id)
        if cust:
            sections.append(
                f"[VERIFIED GROUND TRUTH — CUSTOMER PROFILE]\n"
                f"- Customer ID: {cust['customer_id']}\n"
                f"- Customer Name: {cust['name']}\n"
                f"- Email: {cust['email']}\n"
                f"- Associated Orders: {', '.join(cust['order_ids'])}"
            )

    if not sections:
        sections.append(
            "[VERIFIED GROUND TRUTH DATABASE STATUS]\n"
            "- No specific order_id or tracking_number was provided by the customer yet.\n"
            "- Customer must provide an Order ID (e.g., ORD-2400321) or Tracking Number to retrieve verified records."
        )

    return "\n\n".join(sections)
