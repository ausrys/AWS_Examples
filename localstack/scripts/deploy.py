import time
import os
import boto3
import zipfile
import uuid

LOCALSTACK_URL = "http://localhost:4566"
LAMBDA_ROLE_ARN = "arn:aws:iam::000000000000:role/lambda-role"
LAMBDA_NAME = "GetLambda"
API_NAME = "GetOnlyAPI"


def zip_lambda_code():
    # Zip get_lambda
    with zipfile.ZipFile("get_lambda.zip", "w") as zf:
        zf.write("lambda/get_lambda.py", arcname="get_lambda.py")

        # Add dependencies (for get_lambda)
        lib_dir = "lambda/jwt_layer"
        for root, _, files in os.walk(lib_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, lib_dir)
                zf.write(full_path, arcname=rel_path)

    # Zip process_lambda
    with zipfile.ZipFile("process_lambda.zip", "w") as zf:
        zf.write("lambda/process_lambda.py", arcname="process_lambda.py")


def create_lambda():
    lambda_client = boto3.client(
        "lambda",
        endpoint_url=LOCALSTACK_URL,
        region_name="us-east-1"
    )
    try:
        lambda_client.delete_function(FunctionName=LAMBDA_NAME)
        print(f"Deleted existing Lambda: {LAMBDA_NAME}")
    except lambda_client.exceptions.ResourceNotFoundException:
        pass
    with open("get_lambda.zip", "rb") as f:
        zipped_code = f.read()

    response = lambda_client.create_function(
        FunctionName=LAMBDA_NAME,
        Runtime="python3.9",
        Role=LAMBDA_ROLE_ARN,
        Handler="get_lambda.handler",
        Code={"ZipFile": zipped_code},
        Timeout=10,
        Publish=True,
    )
    print("Lambda created:", response["FunctionArn"])
    return response["FunctionArn"]


def create_api_gateway(lambda_arn):
    apigw = boto3.client(
        "apigateway",
        endpoint_url=LOCALSTACK_URL,
        region_name="us-east-1"  # <-- add this
    )

    # Create REST API
    api = apigw.create_rest_api(name=API_NAME)
    api_id = api["id"]

    # Get root resource id
    resources = apigw.get_resources(restApiId=api_id)
    root_id = resources["items"][0]["id"]

    # Create GET method
    apigw.put_method(
        restApiId=api_id,
        resourceId=root_id,
        httpMethod="GET",
        authorizationType="NONE"
    )

    # Integration
    apigw.put_integration(
        restApiId=api_id,
        resourceId=root_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )

    # Deploy
    apigw.create_deployment(restApiId=api_id, stageName="dev")

    # Add permission so API GW can call Lambda
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name="us-east-1")
    statement_id = f"apigw-access-{uuid.uuid4()}"  # generates a unique ID

    lambda_client.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId=statement_id,
        Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:us-east-1:000000000000:{api_id}/*/GET/"
    )

    print(
        f"API Gateway deployed: http://localhost:4566/restapis/{api_id}/dev/_user_request_")
    return api_id


def create_sqs():
    # Create SQS Queue
    sqs = boto3.client(
        "sqs", endpoint_url=LOCALSTACK_URL, region_name="us-east-1")
    sqs_queue_name = "ai_requests"
    sqs_response = sqs.create_queue(QueueName=sqs_queue_name)
    queue_url = sqs_response["QueueUrl"]
    print(f"SQS queue created: {queue_url}")
    return queue_url


def create_s3_bucket():
    s3 = boto3.client(
        "s3", endpoint_url="http://localhost:4566", region_name="us-east-1")
    s3.create_bucket(Bucket="ai-results-bucket")
    print("S3 bucket created: ai-results-bucket")


def create_dynamodb_table():
    dynamodb = boto3.client(
        "dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1")
    try:
        dynamodb.create_table(
            TableName="ai_results",
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        print("DynamoDB table created: ai_results")
    except dynamodb.exceptions.ResourceInUseException:
        print("DynamoDB table already exists.")


def create_process_lambda():
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name="us-east-1")

    # Delete if exists
    try:
        lambda_client.delete_function(FunctionName="ProcessLambda")
    except lambda_client.exceptions.ResourceNotFoundException:
        pass

    with open("process_lambda.zip", "rb") as f:
        zipped_code = f.read()

    response = lambda_client.create_function(
        FunctionName="ProcessLambda",
        Runtime="python3.9",
        Role=LAMBDA_ROLE_ARN,
        Handler="process_lambda.handler",
        Code={"ZipFile": zipped_code},
        Timeout=60,
        Publish=True,
    )
    print("Process Lambda created:", response["FunctionArn"])
    return response["FunctionArn"]


def attach_sqs_trigger(queue_url):
    lambda_client = boto3.client(
        "lambda", endpoint_url="http://localhost:4566", region_name="us-east-1")
    sqs = boto3.client(
        "sqs", endpoint_url="http://localhost:4566", region_name="us-east-1")

    attributes = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"])
    queue_arn = attributes["Attributes"]["QueueArn"]

    lambda_client.create_event_source_mapping(
        EventSourceArn=queue_arn,
        FunctionName="ProcessLambda",
        Enabled=True,
        BatchSize=1,
    )

    try:
        lambda_client.add_permission(
            FunctionName="ProcessLambda",
            StatementId="sqs-invoke",
            Action="lambda:InvokeFunction",
            Principal="sqs.amazonaws.com",
            SourceArn=queue_arn,
        )
    except lambda_client.exceptions.ResourceConflictException:
        print("Permission already exists")

    print("SQS trigger attached to ProcessLambda.")


def main():
    zip_lambda_code()

    lambda_arn = create_lambda()
    create_api_gateway(lambda_arn)
    queue_url = create_sqs()
    create_s3_bucket()
    create_dynamodb_table()
    process_lambda_arn = create_process_lambda()
    attach_sqs_trigger(queue_url)


if __name__ == "__main__":
    main()
