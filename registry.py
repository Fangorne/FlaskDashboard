import os
from infrastructure.adapters.kafka_adapter import KafkaEventSubscriber
from infrastructure.adapters.mock_adapter import MockEventSubscriber
from core.services import OrderService

def start_all_subscribers():
    # Inversion de contrôle : on choisit l'implémentation dynamiquement
    mode = os.getenv("APP_MODE", "DEV") # DEV ou PROD
    
    if mode == "PROD":
        bus = KafkaEventSubscriber()
    else:
        bus = MockEventSubscriber()
    
    # Le reste du code est IDENTIQUE, peu importe le bus
    bus.listen(
        topic="orders",
        handler=OrderService.process_critical_order,
        filter_func=lambda m: '"priority":"HIGH"' in m
    )
