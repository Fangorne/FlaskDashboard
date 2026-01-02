from core.interfaces import EventSubscriber
from infrastructure.kafka.base import kafka_consumer  # Ton décorateur stratégique

class KafkaConsumerAdapter(EventSubscriber):
    def listen(self, topic: str, handler: callable, rewind_hours: int = 0, filter_func=None):
        # On wrap le handler avec la logique Kafka (Rewind, Offset, Poll)
        run_kafka = kafka_consumer(
            topic=topic, 
            rewind_hours=rewind_hours, 
            filter_func=filter_func
        )(handler)
        
        run_kafka() # Lance la boucle while True
