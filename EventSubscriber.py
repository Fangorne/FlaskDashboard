from abc import ABC, abstractmethod

class EventSubscriber(ABC):
    @abstractmethod
    def listen(self, topic: str, handler: callable, rewind_hours: int = 0, filter_func=None):
        """Contrat imposé à n'importe quel système de messagerie"""
        pass
