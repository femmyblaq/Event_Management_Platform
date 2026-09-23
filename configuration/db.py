from config import Config
import pymysql
def get_connection():
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USERNAME,
        password=Config.DB_PASSWORD,
        database=Config.DB_DATABASE_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection