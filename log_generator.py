#!/usr/bin/env python3
"""Log generator: nested JSON lines via logging."""

import json
import logging
import random
import string
import time
from datetime import datetime

# 24 products total: 6 per area (Bedroom, Kitchen, Front-Room, Hall-Way)
inventory = {
    "Bedroom": {
        "Double Bed": 200,
        "Side stand": 150,
        "Wardrobe": 350,
        "Dressing table": 180,
        "Chest of drawers": 220,
        "Bookshelf": 95,
    },
    "Kitchen": {
        "Cupboard": 100,
        "Fridge": 300,
        "Microwave": 75,
        "Oven": 400,
        "Dishwasher": 350,
        "Kettle": 45,
    },
    "Front-Room": {
        "TV": 600,
        "Sofa": 1000,
        "Arm_chair": 500,
        "Coffee table": 120,
        "Lamp": 65,
        "Rug": 85,
    },
    "Hall-Way": {
        "Carpet": 50,
        "Shoe_rack": 35,
        "Coat_stand": 75,
        "Console table": 140,
        "Mirror": 55,
        "Umbrella stand": 30,
    },
}
STATUSES = ["browsing", "abandoned", "complete"]

# ISO 3166-1 alpha-3 country codes (sample set for random selection)
GEO_CODES = [
    "GBR", "USA", "FRA", "DEU", "ITA", "ESP", "JPN", "AUS", "CAN", "BRA",
    "IND", "CHN", "NLD", "SWE", "NOR", "DNK", "IRL", "POL", "BEL", "CHE",
]

# Name fragments for userid generation (short names / syllables)
USERID_PREFIXES = [
    "Jo", "Steve", "Alex", "Sam", "Kim", "Pat", "Lee", "Max", "Ray", "Jay",
    "Tom", "Ann", "Ben", "Meg", "Dan", "Amy", "Rob", "Eve", "Tim", "Lou",
]

logging.basicConfig(level=logging.INFO, format="%(message)s")


def random_userid():
    """Generate a userid of up to 8 chars, e.g. Jo1982, Steve02."""
    prefix = random.choice(USERID_PREFIXES)
    remaining = 8 - len(prefix)
    if remaining <= 0:
        return prefix[:8]
    # Append digits to fill up to 8 chars
    digits = "".join(random.choices(string.digits, k=min(remaining, 4)))
    return (prefix + digits)[:8]


def main():
    entries = [(d, p, c) for d, items in inventory.items() for p, c in items.items()]
    while True:
        selection = random.sample(entries, random.randint(1, 5))
        total = sum(c for _, _, c in selection)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        userid = random_userid()
        geo = random.choice(GEO_CODES)
        checkout_status = random.choice(STATUSES)
        # One log entry per item (flat for Elastic); same order fields on each line
        for department, product, price in selection:
            payload = {
                "timestamp": timestamp,
                "userid": userid,
                "geo": geo,
                "department": department,
                "product": product,
                "price": price,
                "total": total,
                "checkout_status": checkout_status,
            }
            logging.info(json.dumps(payload))
        time.sleep(10)


if __name__ == "__main__":
    main()
