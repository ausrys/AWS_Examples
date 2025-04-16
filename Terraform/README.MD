# 🛠️ AWS Lambda + API Gateway with Terraform

This project sets up a simple **AWS Lambda function** connected to an **HTTP API Gateway** using **Terraform**. The Lambda echoes back any message you send to it — essentially working as a minimal "echo" service.

---

## 🚀 What This Project Does

- Creates an AWS Lambda function using Python (`main.py`)
- Uses Terraform to define and deploy infrastructure
- Connects the Lambda function to API Gateway
- Exposes a public HTTP endpoint to trigger the function via POST
- Returns the same JSON payload that was sent

---

## 🔍 Testing the Endpoint
- URL -> https://9vft58kvu8.execute-api.eu-north-1.amazonaws.com/echo
- Method -> POST
- Body:
```
{
  "message": "Hello, Lambda!"
}
```
- Response:
```
{
  "message": "Hello, Lambda!"
}
```
