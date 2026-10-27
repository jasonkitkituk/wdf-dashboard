import os
from flask import Flask, render_template, request
from flask import request, jsonify
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


@app.route('/api/player-wld')
def api_player_wld():
    aside = request.args.get('aside', 'all')
    sort1 = request.args.get('sort1', 'point:desc')
    sort2 = request.args.get('sort2', 'avg_point:desc')
    sort3 = request.args.get('sort3', 'total:desc')

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

    def parse_sort(sort_str):
        parts = sort_str.split(':')
        col_key = parts[0] if parts[0] in allowed_columns else 'point'
        direction = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ['ASC', 'DESC'] else 'DESC'
        return allowed_columns[col_key], direction

    col1, dir1 = parse_sort(sort1)
    col2, dir2 = parse_sort(sort2)
    col3, dir3 = parse_sort(sort3)

    # 💡 根據賽制類型動態設定「最小參與場數門檻」與過濾條件
    min_games = 3 if aside == '7' else 6
    
    aside_condition = ""
    query_params = []
    
    if aside in ['7', '9']:
        aside_condition = "AND m.pitch_aside = %s"
        query_params.append(int(aside))

    sql_query = f"""
        SELECT 
            pl.id AS player_id,
            pl.name AS player_name,
            SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS win,
            SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END) AS draw,
            SUM(CASE WHEN mt.result = 'Lose' THEN 1 ELSE 0 END) AS lose,
            COUNT(pms.match_id) AS total,
            SUM(CASE WHEN mt.result IN ('Win', 'Draw') THEN 1 ELSE 0 END) AS unbeaten,
            SUM(CASE 
                WHEN mt.result = 'Win' THEN 3 
                WHEN mt.result = 'Draw' THEN 1 
                ELSE 0 
            END) AS point,
            
            -- 💡 依據選定的賽制使用對應的門檻值 (7-a-side 為 3場，其餘為 6場)
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND(SUM(CASE WHEN mt.result = 'Win' THEN 3 WHEN mt.result = 'Draw' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) ELSE NULL END AS avg_point,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS win_pct,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS draw_pct,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((SUM(CASE WHEN mt.result = 'Lose' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS lose_pct,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((SUM(CASE WHEN mt.result IN ('Win', 'Draw') THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS unbeaten_pct

        FROM 
            player_match_stats pms
        JOIN 
            players pl ON pms.player_id = pl.id
        JOIN 
            match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
        JOIN 
            matches m ON pms.match_id = m.id
        WHERE 
            pl.is_active = true
            {aside_condition}
        GROUP BY 
            pl.id, pl.name
        HAVING 
            COUNT(pms.match_id) > 0
        ORDER BY 
            {col1} {dir1} NULLS LAST,
            {col2} {dir2} NULLS LAST,
            {col3} {dir3} NULLS LAST;
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql_query, tuple(query_params))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(rows)

    except Exception as e:
        print(f"Error in /api/player-wld: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/player-gaos')
def api_player_gaos():
    aside = request.args.get('aside', 'all')
    sort1 = request.args.get('sort1', 'goal:desc')
    sort2 = request.args.get('sort2', 'assist:desc')
    sort3 = request.args.get('sort3', 'total:desc')

    allowed_columns = {
        'player_name': 'pl.name',
        'goal': 'goal',
        'assist': 'assist',
        'ga': 'ga',
        'clean_sheet': 'clean_sheet',
        'own_goal': 'own_goal',
        'goal_conceded': 'goal_conceded',
        'total': 'total',
        'goal_ratio': 'goal_ratio',
        'gc_ratio': 'gc_ratio',
        'ga_ratio': 'ga_ratio'
    }

    def parse_sort(sort_str):
        parts = sort_str.split(':')
        col_key = parts[0] if parts[0] in allowed_columns else 'goal'
        direction = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ['ASC', 'DESC'] else 'DESC'
        return allowed_columns[col_key], direction

    col1, dir1 = parse_sort(sort1)
    col2, dir2 = parse_sort(sort2)
    col3, dir3 = parse_sort(sort3)

    min_games = 3 if aside == '7' else 6

    aside_condition = ""
    if aside in ['7', '9']:
        aside_condition = f"AND m.pitch_aside = {int(aside)}"

    sql_query = f"""
        SELECT 
            pl.id AS player_id,
            pl.name AS player_name,
            COALESCE(SUM(pms.goals), 0) AS goal,
            COALESCE(SUM(pms.assists), 0) AS assist,
            (COALESCE(SUM(pms.goals), 0) + COALESCE(SUM(pms.assists), 0)) AS ga,
            COALESCE(SUM(pms.own_goals), 0) AS own_goal,
            SUM(CASE WHEN pms.clean_sheet = true THEN 1 ELSE 0 END) AS clean_sheet,
            COALESCE(SUM(mt.goals_conceded), 0) AS goal_conceded,
            COUNT(pms.match_id) AS total,
            
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((COALESCE(SUM(pms.goals), 0)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)), 2) ELSE NULL END AS goal_ratio,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND((COALESCE(SUM(mt.goals_conceded), 0)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)), 2) ELSE NULL END AS gc_ratio,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND(((COALESCE(SUM(pms.goals), 0) + COALESCE(SUM(pms.assists), 0))::NUMERIC / NULLIF(COUNT(pms.match_id), 0)), 2) ELSE NULL END AS ga_ratio

        FROM 
            player_match_stats pms
        JOIN 
            players pl ON pms.player_id = pl.id
        JOIN 
            matches m ON pms.match_id = m.id
        JOIN 
            match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
        WHERE 
            pl.is_active = true
            {aside_condition}
        GROUP BY 
            pl.id, pl.name
        HAVING 
            COUNT(pms.match_id) > 0
        ORDER BY 
            {col1} {dir1} NULLS LAST,
            {col2} {dir2} NULLS LAST,
            {col3} {dir3} NULLS LAST;
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)

    except Exception as e:
        print(f"Error in /api/player-gaos: {e}")
        return jsonify({"error": str(e)}), 500

    

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)