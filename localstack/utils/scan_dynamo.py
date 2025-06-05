import boto3


def scan_dynamodb_table():
    dynamodb = boto3.client(
        "dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1"
    )

    response = dynamodb.list_tables()
    print("📋 Tables:", response["TableNames"])
