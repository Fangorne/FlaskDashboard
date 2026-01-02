from infrastructure.adapters.mock_adapter import MockEventSubscriber
from unittest.mock import MagicMock

def test_service_with_custom_scenarios():
    subscriber = MockEventSubscriber()
    mock_service = MagicMock()

    # On injecte un scénario spécifique : une commande corrompue et une commande valide
    my_custom_scenario = [
        '{"id": 99, "priority": "HIGH", "item": "Produit Cassé"}',
        '{"id": 100, "priority": "LOW", "item": "Produit OK"}'
    ]

    subscriber.listen(
        topic="orders",
        handler=mock_service,
        filter_func=lambda m: "HIGH" in m,
        mock_data=my_custom_scenario
    )

    # L'assertion vérifiera que seul le message HIGH (id 99) est passé
    # (Note: en test réel, ajoutez un petit sleep ou un wait si le thread est asynchrone)
