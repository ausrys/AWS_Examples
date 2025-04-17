# 🛠️ AWS Lambda + API Gateway Terraform Setup

This Terraform configuration deploys a serverless Python application on AWS using **Lambda** and exposes it via **API Gateway v2 (HTTP API)**. It also uses a **Lambda Layer** to manage Python dependencies separately from your function code.

---

## 📦 What This Script Does

1. **Creates an IAM Role** for Lambda execution with basic logging permissions.
2. **Packages and deploys a Lambda function** (`main.zip`) using Python 3.11 runtime.
3. **Sets environment variables** including `GEMINI_API_KEY`.
4. **Creates a Lambda Layer** (`python.zip`) that contains Python dependencies.
5. **Attaches the Lambda Layer** to the function.
6. **Creates an HTTP API Gateway** endpoint (`POST /ask`) that triggers the Lambda function.
7. **Grants API Gateway permission** to invoke the Lambda function.
8. **Outputs the API URL** after deployment.

---

## 🔧 Prerequisites

- Terraform installed
- AWS CLI configured with sufficient permissions
- Python 3.x and pip

---

## 📥 How to Prepare Your Lambda Files

- Zip main python file where the function is
```
zip main.zip main.py
```

- Create Lambda Layer Zip
```
pip install requests -t python/
zip -r python.zip python
```
> [!IMPORTANT]
> Zip file must be called "python.zip", otherwise the layer will not recognise it.

## 🚀 Deployment

1. Define API key in terraform.tfvars
```
gemini_api_key = "your_real_api_key"
```

2. Deploy with Terraform
```
terraform init
terraform apply
```

# 🌐 API Usage
- Once deployed, Terraform will output an API endpoint like:

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