#!/usr/bin/env python3
"""Log generator: nested JSON lines via logging."""

import json
import logging
import random
import time
from datetime import datetime

inventory = {
    "Bedroom": {"Double Bed": 200, "Side stand": 150, "Wardrobe": 350},
    "Kitchen": {"cubboard": 100, "Fridge": 300, "Microwave": 75},
    "Front-Room": {"TV": 600, "Sofa": 1000, "Arm_chair": 500},
    "Hall-Way": {"Carpet": 50, "Shoe_rack": 35, "Coat_stand": 75},
}
STATUSES = ["browsing", "abandoned", "complete"]

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    entries = [(d, p, c) for d, items in inventory.items() for p, c in items.items()]
    while True:
        selection = random.sample(entries, random.randint(1, 5))
        total = sum(c for _, _, c in selection)
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{"department": d, "product": p, "price": c} for d, p, c in selection],
            "total": total,
            "checkout_status": random.choice(STATUSES),
        }
        logging.info(json.dumps(payload))
        time.sleep(10)


if __name__ == "__main__":
    main()
