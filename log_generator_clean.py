#!/usr/bin/env python3
"""Log generator: nested JSON lines via logging + curl to Elastic logs-otel (OTLP)."""

import json
import logging
import os
import random
import string
import subprocess
import sys
import time
from datetime import datetime

# Elastic Cloud Hosted: cgi-test-978e05 Managed OTLP (logs-otel)
# Kibana: https://cgi-test-012345.kb.europe-west2.gcp.elastic-cloud.com/v1/logs
# 
ELASTIC_OTLP_LOGS_URL = (
    "https://UPDATE-ELASTIC-URL-FOR_YOUR-CLUSTER/v1/logs"
)
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
OTEL_SERVICE_NAME = "checkout"
# Elastic 9.4 Streams wired endpoint (not a data_stream.dataset name)
OTEL_INDEX = "logs.otel"

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

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def random_userid():
    """Generate a userid of up to 8 chars, e.g. Jo1982, Steve02."""
    prefix = random.choice(USERID_PREFIXES)
    remaining = 8 - len(prefix)
    if remaining <= 0:
        return prefix[:8]
    digits = "".join(random.choices(string.digits, k=min(remaining, 4)))
    return (prefix + digits)[:8]


def _otlp_attr(key, value):
    """Encode a Python value as an OTLP JSON KeyValue."""
    if isinstance(value, bool):
        typed = {"boolValue": value}
    elif isinstance(value, int) and not isinstance(value, bool):
        typed = {"intValue": str(value)}
    elif isinstance(value, float):
        typed = {"doubleValue": value}
    else:
        typed = {"stringValue": str(value)}
    return {"key": key, "value": typed}


def otlp_logs_payload(payloads):
    """Build an OTLP/HTTP JSON ExportLogsServiceRequest for one loop batch."""
    now_ns = str(time.time_ns())
    log_records = []
    for doc in payloads:
        log_records.append(
            {
                "timeUnixNano": now_ns,
                "observedTimeUnixNano": now_ns,
                "severityNumber": 9,
                "severityText": "INFO",
                "body": {"stringValue": json.dumps(doc)},
                "attributes": [_otlp_attr(k, v) for k, v in doc.items()],
            }
        )
    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        _otlp_attr("service.name", OTEL_SERVICE_NAME),
                        _otlp_attr("elasticsearch.index", OTEL_INDEX),
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": "log_generator_curl", "version": "1.0.0"},
                        "logRecords": log_records,
                    }
                ],
            }
        ]
    }


def send_with_curl(payloads):
    """POST this loop's log records to the Managed OTLP logs-otel endpoint via curl."""
    if not payloads:
        return
    if not ELASTIC_API_KEY:
        logging.warning(
            "ELASTIC_API_KEY is not set; skip OTLP send. Export a cgi-test API key, "
            "or set ELASTIC_API_KEY in this script."
        )
        return
    body = json.dumps(otlp_logs_payload(payloads))
    cmd = [
        "curl",
        "-sS",
        "-f",
        "-m", "10",
        "-X", "POST",
        ELASTIC_OTLP_LOGS_URL,
        "-H", f"Authorization: ApiKey {ELASTIC_API_KEY}",
        "-H", "Content-Type: application/json",
        "--data-binary", "@-",
    ]
    try:
        result = subprocess.run(
            cmd,
            input=body.encode("utf-8"),
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logging.warning("Elastic OTLP curl failed: %s", e)
        return
    if result.returncode != 0:
        err = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace").strip()
        logging.warning("Elastic OTLP curl HTTP error: %s", err or f"exit {result.returncode}")


def main():
    if not ELASTIC_API_KEY:
        logging.warning(
            "No API key for cgi-test-978e05. Set ELASTIC_API_KEY before expecting "
            "logs-otel ingest to succeed."
        )
    entries = [(d, p, c) for d, items in inventory.items() for p, c in items.items()]
    while True:
        selection = random.sample(entries, random.randint(1, 5))
        total = sum(c for _, _, c in selection)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        userid = random_userid()
        geo = random.choice(GEO_CODES)
        checkout_status = random.choice(STATUSES)
        payloads = []
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
            payloads.append(payload)
            logging.info(json.dumps(payload))
        send_with_curl(payloads)
        time.sleep(10)


if __name__ == "__main__":
    main()
