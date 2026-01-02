import time
import threading
from core.interfaces import EventSubscriber

class MockEventSubscriber(EventSubscriber):
    def listen(self, topic: str, handler: callable, rewind_hours: int = 0, filter_func=None):
        def simulate():
            print(f"🛠️ [MOCK] Simulation d'écoute sur : {topic}")
            should_include = filter_func or (lambda _: True)
            
            # Simulation de quelques messages de test
            mock_messages = [
                '{"id": 1, "priority": "LOW", "item": "Keyboard"}',
                '{"id": 2, "priority": "HIGH", "item": "Monitor"}',
                '{"id": 3, "priority": "HIGH", "item": "Laptop"}'
            ]

            for raw_payload in mock_messages:
                time.sleep(1) # Simule le délai réseau
                if should_include(raw_payload):
                    print(f"✅ [MOCK] Message accepté par le filtre -> Envoi au service")
                    handler(raw_payload)
                else:
                    print(f"❌ [MOCK] Message rejeté par le filtre")

        # On lance la simulation dans un thread pour ne pas bloquer le démarrage
        threading.Thread(target=simulate, daemon=True).start()
