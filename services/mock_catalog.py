from decimal import Decimal, ROUND_HALF_UP


def money(value: Decimal | int | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


HOME_ITEMS = {
    "sofa": ("Living room", 18000, "IKEA"),
    "bed": ("Bedroom", 16000, "IKEA"),
    "wardrobe": ("Storage", 12000, "Amazon"),
    "lights": ("Lighting", 1800, "Flipkart"),
    "ceiling fan": ("Appliance", 3200, "Amazon"),
    "dining table": ("Dining", 10000, "IKEA"),
    "curtains": ("Decor", 2200, "Flipkart"),
    "wall decoration": ("Decor", 1500, "Amazon"),
    "storage": ("Storage", 3500, "IKEA"),
}

JEWELRY = [
    ("Minimal pendant set", "Necklace", 1800, "Gold-plated alloy", "Gold", "Minimal"),
    ("Pearl drop earrings", "Earrings", 2400, "Freshwater pearl", "Ivory", "Classic"),
    ("Color-pop bangle pair", "Bracelet", 1200, "Brass", "Multicolor", "Contemporary"),
]


def home_recommendations(payload: dict) -> dict:
    budget = money(payload["total_budget"])
    items = payload.get("items", [])
    count = max(len([item for item in items if item.get("quantity", 0) > 0]), 1)
    recommendations = []
    for item in items:
        quantity = int(item.get("quantity", 0))
        if quantity <= 0:
            continue
        name = item["name"].strip()
        category, base_price, platform = HOME_ITEMS.get(name.lower(), ("Home decor", 2500, "Amazon"))
        unit_price = money(min(Decimal(base_price), budget * Decimal("0.72") / count / quantity))
        total = money(unit_price * quantity)
        recommendations.append({
            "name": name.title(), "category": category, "estimated_price": unit_price,
            "quantity": quantity, "estimated_total": total, "platform": platform,
            "reason": f"A practical {payload['style_preference']} option sized to your requested quantity.",
            "style": payload["style_preference"], "budget_status": "within", "product_url": None,
        })
    total = money(sum((row["estimated_total"] for row in recommendations), Decimal(0)))
    return {"summary": f"A {payload['style_preference']} starter plan for your {payload['home_type']}.", "recommendations": recommendations,
            "total_estimated": total, "remaining_budget": money(budget - total)}


def party_recommendations(payload: dict) -> dict:
    budget = money(payload["total_budget"])
    allocations = [("Catering", 0.40), ("Decoration", 0.18), ("Venue", 0.22), ("Entertainment", 0.12), ("Accommodation", 0.08 if payload.get("accommodation_required") else 0)]
    vendors = {"Catering": "Local catering estimate", "Decoration": "Local decor vendor", "Venue": "Community venue estimate", "Entertainment": "Local event vendor", "Accommodation": "OYO (example source)"}
    recommendations = []
    for category, share in allocations:
        if share == 0:
            continue
        amount = money(budget * Decimal(str(share)))
        recommendations.append({"name": f"{category} plan", "category": category, "estimated_price": amount,
            "quantity": 1, "estimated_total": amount, "platform": vendors[category],
            "reason": f"Estimated for {payload['guest_count']} guests; confirm availability and final quotes directly.",
            "style": payload["event_type"], "budget_status": "within", "product_url": None,
            "guest_capacity": payload["guest_count"]})
    total = money(sum((row["estimated_total"] for row in recommendations), Decimal(0)))
    return {"summary": f"A preliminary {payload['event_type']} budget for {payload['guest_count']} guests.",
            "allocations": [{"category": name, "amount": money(budget * Decimal(str(share)))} for name, share in allocations if share],
            "recommendations": recommendations, "total_estimated": total, "remaining_budget": money(budget - total)}


def jewelry_recommendations(payload: dict, outfit_analysis: str = "") -> dict:
    budget = money(payload["budget"])
    remaining = budget
    recommendations = []
    for name, kind, price, material, color, style in JEWELRY:
        if payload["jewelry_type"].lower() not in {"any", "set"} and payload["jewelry_type"].lower() not in kind.lower():
            continue
        if remaining <= 0:
            break
        if payload["preferred_material"].lower() not in {"any", material.lower()}:
            material = payload["preferred_material"]
        chosen_color = payload["color_preference"] if payload["color_preference"].lower() != "any" else color
        amount = money(min(Decimal(price), remaining))
        recommendations.append({"name": name, "category": kind, "estimated_price": amount, "quantity": 1,
            "estimated_total": amount, "platform": "Local jewelry catalog", "reason": f"Coordinates with your {payload['occasion']} occasion and {payload['style_preference']} preference. {outfit_analysis}".strip(),
            "style": payload["style_preference"], "material": material, "color": chosen_color, "occasion": payload["occasion"],
            "budget_status": "within", "product_url": None})
        remaining = money(remaining - amount)
    recommendations = recommendations or [{"name": "Everyday accessory", "category": payload["jewelry_type"], "estimated_price": money(min(500, budget)),
        "quantity": 1, "estimated_total": money(min(500, budget)), "platform": "Local jewelry catalog", "reason": "A simple option within your budget.",
        "style": payload["style_preference"], "material": payload["preferred_material"], "color": payload["color_preference"], "occasion": payload["occasion"],
        "budget_status": "within", "product_url": None}]
    total = money(sum((row["estimated_total"] for row in recommendations), Decimal(0)))
    return {"summary": f"Jewelry ideas for {payload['occasion']}, guided by your budget and preferences.", "recommendations": recommendations,
            "total_estimated": total, "remaining_budget": money(budget - total)}