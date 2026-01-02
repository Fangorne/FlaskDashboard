from infrastructure.kafka.base import kafka_consumer # On réutilise notre décorateur
from core.interfaces import EventSubscriber

class KafkaEventSubscriber(EventSubscriber):
    def listen(self, topic: str, handler: callable, rewind_hours: int = 0, filter_func=None):
        # On applique dynamiquement le décorateur à la fonction handler
        decorated_handler = kafka_consumer(
            topic=topic, 
            rewind_hours=rewind_hours, 
            filter_func=filter_func
        )(handler)
        
        # On lance l'écoute
        decorated_handler()
