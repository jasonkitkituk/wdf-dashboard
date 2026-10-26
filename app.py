import os
from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

# 填入你的 Supabase 連線字串 (記得換上你的密碼與專案 ID)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    #"postgresql://postgres.你的專案ID:你的密碼@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require"
     "postgresql://postgres:www.WDF123.com@db.pdmcmmibyyjjelwmcgjs.supabase.co:5432/postgres"
)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/')
def index():
    # 預設為 7SIDE，可透過網址參數切換 ?type=7SIDE 或 ?type=9SIDE
    match_type = request.args.get('type', '7SIDE')
    
    rows = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 查詢對應類型的數據 (請根據你的實際 Table 欄位名稱調整 SQL)
        cur.execute("SELECT * FROM matches WHERE pitch_aside = %s;", (match_type,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"資料庫連線錯誤: {e}")

    return render_template('index.html', rows=rows, match_type=match_type)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)