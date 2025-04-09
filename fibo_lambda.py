import json

cache: dict = {}


def recur_fibo(n: int) -> int:

    # Check if the value is already cached
    if n in cache:
        return cache[n]

    if n <= 1:
        return n
    # Compute and cache the Fibonacci value
    result = recur_fibo(n - 1) + recur_fibo(n - 2)
    cache[n] = result
    return cache[n]


def lambda_handler(event):
    if 'queryStringParameters' not in event:
        return {
            'statusCode': 400,
            'body': "Please provide the parameter 'number' "
        }
    if 'number' in event['queryStringParameters']\
            and event['queryStringParameters']['number'].isdigit():

        number = int(event['queryStringParameters']['number'])
        result = recur_fibo(number)
        return {
            'statusCode': 200,
            'body': json.dumps({'result': result})
        }
    return {
        'statusCode': 400,
        'body': "Please enter a number or please provide\
            the parameter 'number'"
    }
