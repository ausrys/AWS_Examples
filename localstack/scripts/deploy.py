import os
import zipfile
import boto3
REGION = "us-east-1"
LOCALSTACK_URL = "http://localhost:4566"

LAMBDA_ROLE_ARN = "arn:aws:iam::000000000000:role/lambda-role"


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
        lib_dir = "lambda/process_layer"
        for root, _, files in os.walk(lib_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, lib_dir)
                zf.write(full_path, arcname=rel_path)

    # Zip event lambda
    with zipfile.ZipFile("event_lambda.zip", "w") as zf:
        zf.write("lambda/event_lambda.py", arcname="event_lambda.py")
        for root, _, files in os.walk("lambda/kafka_layer"):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, "lambda/kafka_layer")
                zf.write(full_path, arcname=rel_path)


def create_s3_bucket():
    s3 = boto3.client("s3", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    s3.create_bucket(Bucket="ai-results-bucket")
    print("✅ S3 bucket created")


def create_sqs():
    sqs = boto3.client("sqs", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    response = sqs.create_queue(QueueName="ai_requests")
    print("✅ SQS queue created")
    return response["QueueUrl"]


def create_dynamodb_table():
    dynamodb = boto3.client(
        "dynamodb", endpoint_url="http://localhost:4566", region_name="us-east-1")

    table_name = "ai_results"

    # Check if the table already exists
    try:
        dynamodb.describe_table(TableName=table_name)
        print(f"✅ DynamoDB table already exists: {table_name}")
        return
    except dynamodb.exceptions.ResourceNotFoundException:
        pass  # Table doesn't exist, continue to create it

    response = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    print(f"✅ DynamoDB table created: {table_name}")


def create_lambda(name, zip_file, handler):
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    try:
        lambda_client.delete_function(FunctionName=name)
    except lambda_client.exceptions.ResourceNotFoundException:
        pass

    with open(zip_file, "rb") as f:
        zipped_code = f.read()

    lambda_client.create_function(
        FunctionName=name,
        Runtime="python3.11",
        Role=LAMBDA_ROLE_ARN,
        Handler=handler,  # ✅ Use the passed-in value
        Code={"ZipFile": zipped_code},
        Timeout=60 if name == "ProcessLambda" else 30,
        Publish=True
    )
    print(f"✅ Lambda {name} created")


def attach_sqs_trigger(queue_url):
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    sqs = boto3.client("sqs", endpoint_url=LOCALSTACK_URL, region_name=REGION)

    attrs = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"])
    queue_arn = attrs["Attributes"]["QueueArn"]
    mappings = lambda_client.list_event_source_mappings(
        FunctionName="ProcessLambda")["EventSourceMappings"]
    for mapping in mappings:
        uuid = mapping["UUID"]
        lambda_client.delete_event_source_mapping(UUID=uuid)
        print(f"❌ Deleted existing event source mapping: {uuid}")
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
            SourceArn=queue_arn
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass

    print("✅ SQS trigger attached to ProcessLambda")


def create_apigateway(lambda_name):
    apigw = boto3.client(
        "apigateway", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name=REGION)

    # ✅ Check for existing API by name
    existing_apis = apigw.get_rest_apis()["items"]
    for api in existing_apis:
        if api["name"] == "GetOnlyAPI":
            api_id = api["id"]
            break
    else:
        # ❌ Not found, so create
        api = apigw.create_rest_api(name="GetOnlyAPI")
        api_id = api["id"]

    lambda_arn = lambda_client.get_function(FunctionName=lambda_name)[
        "Configuration"]["FunctionArn"]
    resources = apigw.get_resources(restApiId=api_id)
    root_id = resources["items"][0]["id"]

    # 🧠 Safe: check if method already exists to avoid duplicate error
    try:
        apigw.put_method(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="GET",
            authorizationType="NONE"
        )
    except apigw.exceptions.ConflictException:
        pass  # Method already exists

    apigw.put_integration(
        restApiId=api_id,
        resourceId=root_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    apigw.create_deployment(
        restApiId=api_id,
        stageName="dev"
    )
    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId="apigw-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:000000000000:{api_id}/*/GET/"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass  # Permission already exists

    print(
        f"API Gateway deployed: http://localhost:4566/restapis/{api_id}/dev/_user_request_")
    return api_id


def create_eventbridge_rule(lambda_name):
    events = boto3.client(
        "events", endpoint_url=LOCALSTACK_URL, region_name=REGION)
    lambda_client = boto3.client(
        "lambda", endpoint_url=LOCALSTACK_URL, region_name=REGION)

    rule_name = "Every2MinRule"
    schedule_expression = "rate(2 minutes)"

    # Create the EventBridge rule
    rule_response = events.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule_expression,
        State="ENABLED"
    )

    rule_arn = rule_response["RuleArn"]

    # Add Lambda permission so EventBridge can invoke it
    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId="eventbridge-invoke",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_arn,
        )
    except lambda_client.exceptions.ResourceConflictException:
        # Permission already exists
        pass

    # Add the Lambda target to the EventBridge rule
    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": "1",
                "Arn": lambda_client.get_function(FunctionName=lambda_name)["Configuration"]["FunctionArn"]
            }
        ]
    )

    print(
        f"✅ EventBridge rule created: {rule_name} triggers {lambda_name} every 2 minutes")


def main():
    zip_lambda_code()
    create_s3_bucket()
    queue_url = create_sqs()
    create_dynamodb_table()

    create_lambda("GetLambda", 'get_lambda.zip', "get_lambda.handler")
    create_lambda("ProcessLambda", 'process_lambda.zip',
                  "process_lambda.handler")
    create_lambda("EventLambda", 'event_lambda.zip', "event_lambda.handler")

    attach_sqs_trigger(queue_url)
    create_apigateway("GetLambda")
    create_eventbridge_rule("EventLambda")


if __name__ == "__main__":
    main()
