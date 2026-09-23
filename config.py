import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    DB_HOST = os.getenv("MYSQL_HOST")
    DB_USERNAME = os.getenv("MYSQL_USERNAME")
    DB_PASSWORD =  os.getenv("MYSQL_PASSWORD")
    DB_PORT = int(os.getenv("MYSQL_PORT"))
    DB_DATABASE_NAME = os.getenv("MYSQL_DB_NAME")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_FROM_TITLE = os.getenv("MAIL_FROM_TITLE")
    

