import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    API_PORT: int = 8000
    
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9093"
    KAFKA_GROUP_ID: str = "my_app_group"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SASL_USER: str = ""
    KAFKA_SASL_PASSWORD: str = ""

    # Chargement du fichier .env
    model_config = SettingsConfigDict(env_file=".env")

# Instance unique pour tout le projet
settings = Settings()

# Dictionnaire prêt à l'emploi pour confluent-kafka
KAFKA_CONFIG = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': settings.KAFKA_GROUP_ID,
    'auto.offset.reset': 'earliest',
}

# Ajout dynamique de la sécurité si nécessaire
if settings.KAFKA_SECURITY_PROTOCOL == "SASL_SSL":
    KAFKA_CONFIG.update({
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
        'sasl.username': settings.KAFKA_SASL_USER,
        'sasl.password': settings.KAFKA_SASL_PASSWORD,
    })
