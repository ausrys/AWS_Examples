# 🛠️ GITHUB CI/CD AWS Lambda + API Gateway Terraform Setup

This Terraform configuration deploys a serverless Python application on AWS using **Lambda** and exposes it via **API Gateway v2 (HTTP API)**. It also uses a **Lambda Layer** to manage Python dependencies separately from your function code.

---

## 📦 CI/CD
1. Watches changes on provided directory.
2. Creates ubuntu machine.
3. Sets up python.
4. Install dependencies from requirmenets.txt into /python folder.
5. Zips main.py and /python folder.
6. Set up Terraform.
7. Configure AWS credentials.
8. Runs terraform init, plan and apply commands.

---

## 📦 Terraform

1. **Creates an IAM Role** for Lambda execution with basic logging permissions.
2. **Packages and deploys a Lambda function** (`main.zip`) using Python 3.11 runtime.
3. **Sets environment variables** including `GEMINI_API_KEY`from github secrets.
4. **Creates a Lambda Layer** (`python.zip`) that contains Python dependencies.
5. **Attaches the Lambda Layer** to the function.
6. **Creates an HTTP API Gateway** endpoint (`POST /ask`) that triggers the Lambda function.
7. **Grants API Gateway permission** to invoke the Lambda function.
---

## 🚀 Deployment

1. Set secret keys in the github secrets.
2. Push the code.


# 🌐 API Usage
- Once deployed, Terraform will output an API endpoint like (you can find the url in the actions):

```
https://xyz123.execute-api.eu-north-1.amazonaws.com/ask
```

- You can now send a POST request to this endpoint with this format:

```
{
  "input": "What is the speed of light?"
}
```

## 🧽 Cleanup

```
terraform destroy
```