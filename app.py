import os
from flask import Flask, render_template, request
#from flask import request, jsonify
#from itertools import combinations
#from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras



from routes.part_routes import part_bp
from routes.wld_routes import wld_bp
from routes.gaos_routes import gaos_bp
from routes.rank_routes import rank_bp


app = Flask(__name__)

app.register_blueprint(part_bp)
app.register_blueprint(wld_bp)
app.register_blueprint(gaos_bp)
app.register_blueprint(rank_bp)




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
    rank_winpct_overall = []
    rank_winpct_9side = []
    rank_winpct_7side = []


    # 💡 宣告變數儲存資料日期範圍預設值
    date_range = {"from_date": "N/A", "end_date": "N/A"}

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 0. 查詢 matches 表格最早與最遲的日期
        cur.execute("SELECT MIN(match_date) AS min_date, MAX(match_date) AS max_date FROM matches;")
        date_res = cur.fetchone()
        if date_res and date_res.get('min_date') and date_res.get('max_date'):
            # 💡 將日期格式化為 DD-MMM-YYYY (例如: 27-Nov-2025)
            date_range["from_date"] = date_res['min_date'].strftime('%d-%b-%Y')
            date_range["end_date"] = date_res['max_date'].strftime('%d-%b-%Y')
        
        # 1. 讀取並執行第一個 SQL (format_stats.sql)
        sql_format = load_sql_query('format_stats.sql')
        cur.execute(sql_format)
        format_stats = cur.fetchone() # 取得一筆加總結果
        
        sql_team = load_sql_query('team_color_stats.sql')
        cur.execute(sql_team)
        team_stats = cur.fetchone() # 取得一筆加總結果

        cur.execute(load_sql_query('location_stats.sql'))
        location_stats = cur.fetchall()

        # 2. 讀取並執行 Rank Top 20 (Most Wins) 的 SQL
        cur.execute(load_sql_query('rank_win_overall.sql'))
        rank_win_overall = cur.fetchall()

        cur.execute(load_sql_query('rank_win_9aside.sql'))
        rank_win_9side = cur.fetchall()

        cur.execute(load_sql_query('rank_win_7aside.sql'))
        rank_win_7side = cur.fetchall()

        cur.execute(load_sql_query('rank_winpct_overall.sql'))
        rank_winpct_overall = cur.fetchall()

        cur.execute(load_sql_query('rank_winpct_9aside.sql'))
        rank_winpct_9side = cur.fetchall()

        cur.execute(load_sql_query('rank_winpct_7aside.sql'))
        rank_winpct_7side = cur.fetchall()



        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"資料庫查詢錯誤: {e}")

    # 渲染首頁並傳入兩個統計資料物件
    return render_template(
        'index.html', 
        format_stats=format_stats, 
        team_stats=team_stats,
        location_stats=location_stats,
        rank_overall=rank_win_overall,
        rank_9side=rank_win_9side,
        rank_7side=rank_win_7side,
        winpct_overall=rank_winpct_overall,
        winpct_9side=rank_winpct_9side,
        winpct_7side=rank_winpct_7side,
        date_range=date_range
    )





if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)