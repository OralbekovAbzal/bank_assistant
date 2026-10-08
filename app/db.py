from dotenv import load_dotenv
import psycopg
import os

load_dotenv()

conn = psycopg.connect(dbname = "bank_assistant", host = "localhost", user = "admin", password = os.getenv("DB_PASSWORD"), port = "5433", autocommit=True)