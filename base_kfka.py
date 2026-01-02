import functools
import time
from confluent_kafka import Consumer, TopicPartition
from config import KAFKA_CONFIG

# --- Stratégies de connexion ---
def setup_standard(consumer, topic, **_):
    consumer.subscribe([topic])
    return f"🚀 Mode Standard sur {topic}"

def setup_rewind(consumer, topic, rewind_hours):
    timestamp_ms = int((time.time() - (rewind_hours * 3600)) * 1000)
    meta = consumer.list_topics(topic, timeout=10)
    partitions = meta.topics[topic].partitions.keys()
    
    search_targets = [TopicPartition(topic, p, timestamp_ms) for p in partitions]
    offsets = consumer.offsets_for_times(search_targets)
    
    consumer.assign(offsets)
    return f"🕒 Mode Rewind (-{rewind_hours}h) sur {topic}"

# --- Le Décorateur ---
def kafka_consumer(topic: str, rewind_hours: int = 0, filter_func=None):
    strategies = {False: setup_standard, True: setup_rewind}
    should_include = filter_func or (lambda _: True)

    def decorator(func):
        @functools.wraps(func)
        def wrapper():
            is_rewind = rewind_hours > 0
            conf = KAFKA_CONFIG.copy()
            if is_rewind:
                conf['group.id'] += f"_rewind_{int(time.time())}"

            consumer = Consumer(conf)
            try:
                log_msg = strategies[is_rewind](consumer, topic, rewind_hours=rewind_hours)
                print(log_msg)

                while True:
                    msg = consumer.poll(1.0)
                    if msg is None or msg.error(): continue

                    payload = msg.value().decode('utf-8')
                    
                    # Application du filtre (Pointeur de fonction)
                    if should_include(payload):
                        func(payload)
            finally:
                consumer.close()
        return wrapper
    return decorator
