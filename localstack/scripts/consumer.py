from kafka import KafkaConsumer
import json
import time

TOPIC_NAME = "ai_events"
KAFKA_BROKER = "kafka:29092"
print("Started")
while True:
    try:
        consumer = KafkaConsumer(
            "ai_events",
            bootstrap_servers=["kafka:29092"],
            group_id="dev-group-1",  # change this to a new name if needed
            auto_offset_reset="earliest",  # reads from beginning if no offset
            enable_auto_commit=False,      # disable auto commit for full
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        print(f"✅ Connected to Kafka, listening to '{TOPIC_NAME}'...")
        break
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}. Retrying in 5s...")
        time.sleep(5)
print("Assigned partitions:", consumer.assignment())
print("👂 Waiting for messages...")
for message in consumer:
    print("✅ Decoded message:", message.value)
