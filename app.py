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
        rank_overall=rank_win_overall,
        rank_9side=rank_win_9side,
        rank_7side=rank_win_7side,
        winpct_overall=rank_winpct_overall,
        winpct_9side=rank_winpct_9side,
        winpct_7side=rank_winpct_7side
    )


@app.route('/player-wld-stats')
def player_wld_stats():
    # 1. 取得前端傳來的參數（預設為 overall 與依 point 排序）
    aside = request.args.get('aside', 'all')  # 可選 'all', '9', '7'
    
    # 用戶最多可以選三個排序欄位與方向 (例如 sort1=point:desc, sort2=win:desc, sort3=total:desc)
    sort_1 = request.args.get('sort1', 'point:desc')
    sort_2 = request.args.get('sort2', 'avg_point:desc')
    sort_3 = request.args.get('sort3', 'total:desc')

    # 2. 建立合法欄位白名單 (防止 SQL Injection)
    allowed_columns = {
        'player_name': 'pl.name',
        'win': 'win',
        'draw': 'draw',
        'lose': 'lose',
        'total': 'total',
        'unbeaten': 'unbeaten',
        'point': 'point',
        'avg_point': 'avg_point',
        'win_pct': 'win_pct',
        'draw_pct': 'draw_pct',
        'lose_pct': 'lose_pct',
        'unbeaten_pct': 'unbeaten_pct'
    }

    def parse_sort_param(sort_str):
        parts = sort_str.split(':')
        col = parts[0] if parts[0] in allowed_columns else 'point'
        direction = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ['ASC', 'DESC'] else 'DESC'
        return allowed_columns[col], direction

    col1, dir1 = parse_sort_param(sort_1)
    col2, dir2 = parse_sort_param(sort_2)
    col3, dir3 = parse_sort_param(sort_3)

    # 3. 讀取並動態組合 SQL
    with open('sql/player_wld_dynamic.sql', 'r') as f:
        sql_query = f.read()

    formatted_sql = sql_query.format(
        sort_col_1=col1, sort_dir_1=dir1,
        sort_col_2=col2, sort_dir_2=dir2,
        sort_col_3=col3, sort_dir_3=dir3
    )

    # 4. 執行查詢並回傳給前端 (以 Supabase 或 Psycopg2 為例)
    # 傳入 aside 參數：若是 overall 傳 'all'，9-a-side 傳 9，7-a-side 傳 7
    # ...執行查詢邏輯...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)