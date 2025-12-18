socle-kafka-python/
├── app/
│ ├── core/
│ │ ├── interfaces/
│ │ │ ├── consumer.py
│ │ │ ├── writer.py
│ │ │ └── secret_provider.py
│ │ ├── pipeline/
│ │ │ ├── transformer.py
│ │ │ └── pipeline.py
│ │ ├── validators/
│ │ │ └── payload.py
│ │ └── errors.py
│ │
│ ├── application/
│ │ ├── services/
│ │ │ └── message_processor.py
│ │ └── consumers/
│ │ └── kafka_runner.py
│ │
│ ├── infrastructure/
│ │ ├── kafka/
│ │ │ └── kafka_consumer.py
│ │ ├── filesystem/
│ │ │ └── file_writer.py
│ │ ├── database/
│ │ │ └── db_writer.py
│ │ ├── vault/
│ │ │ └── vault_client.py
│ │ └── logging/
│ │ └── logger.py
│ │
│ ├── api/
│ │ ├── main.py
│ │── routes/
│ │ └── dependencies.py
│ │
│ └── config/
│ └── settings.py
│
├── tests/
│ ├── unit/
│ │ ├── core/
│ │ └── application/
│ │ └── test_message_processor.py
│ │
│ ├── integration/
│ └── mocks/
│ └── kafka.py
│
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore ├
