# db.py
import os
import psycopg2
import psycopg2.extras

# 優先讀取 Render 環境變數的 DATABASE_URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:www.WDF123.com@db.pdmcmmibyyjjelwmcgjs.supabase.co:5432/postgres"
)

def get_db_connection():
    """建立並回傳帶有 RealDictCursor 的資料庫連線"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn