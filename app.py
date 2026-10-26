import os
from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# 優先讀取 Render 環境變數的 DATABASE_URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:www.WDF123.com@db.pdmcmmibyyjjelwmcgjs.supabase.co:5432/postgres"
)

def get_db_connection():
    # 使用 RealDictCursor 讓查詢結果能以字典/欄位名稱存取
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def load_sql_query(filename):
    path = os.path.join('sql', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/')
def index():
    format_stats = None
    team_stats = None
    rank_overall = []
    rank_9side = []
    rank_7side = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. 讀取並執行第一個 SQL (format_stats.sql)
        sql_format = load_sql_query('format_stats.sql')
        cur.execute(sql_format)
        format_stats = cur.fetchone() # 取得一筆加總結果
        
        # 2. 讀取並執行第二個 SQL (team_color_stats.sql)
        sql_team = load_sql_query('team_color_stats.sql')
        cur.execute(sql_team)
        team_stats = cur.fetchone() # 取得一筆加總結果

        # 2. 讀取並執行 Rank Top 20 (Most Wins) 的 SQL
        cur.execute(load_sql_query('rank_win_overall.sql'))
        rank_overall = cur.fetchall()

        cur.execute(load_sql_query('rank_win_9aside.sql'))
        rank_9side = cur.fetchall()

        cur.execute(load_sql_query('rank_win_7aside.sql'))
        rank_7side = cur.fetchall()
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"資料庫查詢錯誤: {e}")

    # 渲染首頁並傳入兩個統計資料物件
    return render_template(
        'index.html', 
        format_stats=format_stats, 
        team_stats=team_stats,
        rank_overall=rank_overall,
        rank_9side=rank_9side,
        rank_7side=rank_7side
    )


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)