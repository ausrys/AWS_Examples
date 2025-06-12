import json
import boto3
from kafka import KafkaProducer

s3 = boto3.client("s3",
                  region_name="us-east-1")
dynamodb = boto3.resource(
    "dynamodb", region_name="us-east-1")

TABLE_NAME = "ai_results"
BUCKET_NAME = "ai-results-bucket"
KAFKA_TOPIC = "ai_events"
KAFKA_BROKER = "kafka:9092"  # internal name inside Docker network
# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers="http://kafka:29092",
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    items = response.get("Items", [])

    for item in items:
        file_key = item["s3_file"]
        user_id = item["user_id"]

        # Get S3 file content
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
            result_text = obj["Body"].read().decode("utf-8")
        except Exception as e:
            print(f"❌ Failed to read S3 file {file_key}: {e}")
            continue

        # Combine and send to Kafka
        message = {
            "user_id": user_id,
            "timestamp": item["timestamp"],
            "action": item["action"],
            "original_text": item["original_text"],
            "result_text": result_text,
        }

        try:
            producer.send(KAFKA_TOPIC, message)
            print(f"✅ Sent to Kafka: {message}")
        except Exception as e:
            print(f"❌ Failed to send to Kafka: {e}")
