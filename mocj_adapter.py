class MockEventSubscriber(EventSubscriber):
    def __init__(self, default_messages=None):
        # On peut définir des messages globaux à l'initialisation
        self.default_messages = default_messages or [
            '{"id": 1, "priority": "LOW", "item": "Standard Keyboard"}',
            '{"id": 2, "priority": "HIGH", "item": "Gaming Monitor"}',
            '{"id": 3, "priority": "HIGH", "item": "MacBook Pro"}'
        ]

    def listen(self, topic: str, handler: callable, rewind_hours: int = 0, filter_func=None, mock_data=None):
        """
        :param mock_data: Liste de strings JSON personnalisée pour ce flux précis.
        """
        # On utilise les données passées ou les données par défaut
        messages_to_inject = mock_data or self.default_messages
        should_include = filter_func or (lambda _: True)

        def simulate():
            print(f"🛠️  [MOCK] Démarrage du flux sur : {topic}")
            
            for raw_payload in messages_to_inject:
                time.sleep(0.5)  # Simulation d'un flux rapide
                
                if should_include(raw_payload):
                    # Simulation de la transformation en dictionnaire (comme le ferait l'adaptateur Kafka)
                    data = json.loads(raw_payload)
                    handler(data)
                else:
                    print(f"🤫 [MOCK] Message filtré (ignoré) : {raw_payload[:40]}...")

        # Lancement asynchrone pour simuler le comportement non-bloquant de Kafka
        threading.Thread(target=simulate, daemon=True).start()
