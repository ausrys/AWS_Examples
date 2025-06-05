import jwt

SECRET = "your_jwt_secret"

token = jwt.encode({"user_id": "123"}, SECRET, algorithm="HS256")
print("JWT Token:", token)
