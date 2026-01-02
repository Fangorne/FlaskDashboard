import pytest
from unittest.mock import MagicMock
from infrastructure.adapters.mock_adapter import MockEventSubscriber

def test_order_service_filtering_logic():
    """Vérifie que le service ne reçoit que les messages HIGH priority"""
    
    # 1. On Mock le service métier (le Core)
    mock_service_handler = MagicMock()
    
    # 2. On instancie notre abonné de simulation
    subscriber = MockEventSubscriber()
    
    # 3. Définition d'un filtre (Pointeur de fonction)
    def high_priority_only(msg):
        return '"priority": "HIGH"' in msg

    # 4. On lance l'écoute (le mock va injecter 3 messages prédéfinis)
    # Dans le Mock, les messages sont : LOW, HIGH, HIGH
    subscriber.listen(
        topic="test_topic",
        handler=mock_service_handler,
        filter_func=high_priority_only
    )

    # 5. Assertions
    # Le service doit avoir été appelé exactement 2 fois (pour les 2 HIGH)
    assert mock_service_handler.call_count == 2
    
    # On vérifie que le premier appel était bien le Monitor (le premier HIGH)
    first_call_args = mock_service_handler.call_args_list[0][0][0]
    assert "Monitor" in first_call_args
