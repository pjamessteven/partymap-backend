import os

# Broker settings
broker_url = "amqp://%s:%s@%s:%s//" % (os.getenv("RABBITMQ_DEFAULT_USER", ""), os.getenv(
        "RABBITMQ_DEFAULT_PASS", ""), os.getenv("RABBIT_MQ_HOSTNAME", ""),  os.getenv("RABBIT_MQ_PORT", "")) 

# Result backend settings
result_backend = "rpc://"

# List of modules to import when the Celery worker starts
imports = ('pmapi.tasks',)