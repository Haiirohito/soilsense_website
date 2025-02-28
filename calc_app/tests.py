from django.test import TestCase
import jwt as pyjwt
import os
from dotenv import load_dotenv

load_dotenv()

# Create your tests here.
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiODJmNzBlMTEtMGJmYS00MTZhLTk3YTEtZGFiODAxMmMyMTJkIiwidXNlcm5hbWUiOiJkZXZkZWVwIiwiZXhwIjoxNzQxMDg2NjI5fQ.U8i9MsFO-eveXsw_wPRyc26s-4TPzX4XVO2XhHed7UE"
decoded = pyjwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
print(decoded)