import json
from infrastructure.kafka.base import kafka_consumer
from core.services import OrderService

# --- Filtres (Pointeurs de fonction) ---
def is_high_priority(raw_payload):
    try:
        data = json.loads(raw_payload)
        return data.get("priority") == "HIGH"
    except:
        return False

# --- Implémentations ---
@kafka_consumer(topic="orders", filter_func=is_high_priority)
def high_priority_worker(data):
    OrderService.process_critical_order(data)

@kafka_consumer(topic="orders", rewind_hours=24)
def history_archive_worker(data):
    OrderService.archive_order(data)
