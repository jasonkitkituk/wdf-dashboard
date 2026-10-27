import os
from flask import Flask, render_template, request
from flask import request, jsonify
from itertools import combinations
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
    #sort2 = request.args.get('sort2', 'avg_point:desc')
    #sort3 = request.args.get('sort3', 'total:desc')

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
    #col2, dir2 = parse_sort(sort2)
    #col3, dir3 = parse_sort(sort3)

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
            {col1} {dir1} NULLS LAST;
            
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
    sort1 = request.args.get('sort1', 'player_name:asc')

    allowed_columns = {
        'player_name': 'pl.name',
        'goal': 'goal',
        'assist': 'assist',
        'ga': 'ga',
        'own_goal': 'own_goal',
        'clean_sheet': 'clean_sheet',
        'goal_conceded': 'goal_conceded',
        'total': 'total',
        'goal_ratio': 'goal_ratio',
        'gc_ratio': 'gc_ratio',
        'ga_ratio': 'ga_ratio'
    }

    def parse_sort(sort_str):
        parts = sort_str.split(':')
        col_key = parts[0] if parts[0] in allowed_columns else 'player_name'
        direction = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ['ASC', 'DESC'] else 'ASC'
        return allowed_columns[col_key], direction

    col1, dir1 = parse_sort(sort1)
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
            COALESCE(SUM(pms.goals), 0) AS goal,
            COALESCE(SUM(pms.assists), 0) AS assist,
            COALESCE(SUM(pms.goals + pms.assists), 0) AS ga,
            COALESCE(SUM(pms.own_goals), 0) AS own_goal,
            COALESCE(SUM(CASE WHEN pms.clean_sheet = true THEN 1 ELSE 0 END), 0) AS clean_sheet,
            COALESCE(SUM(mt.goals_conceded), 0) AS goal_conceded,
            COUNT(pms.match_id) AS total,
            
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND(SUM(pms.goals)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) ELSE NULL END AS goal_ratio,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND(SUM(mt.goals_conceded)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) ELSE NULL END AS gc_ratio,
            CASE WHEN COUNT(pms.match_id) >= {min_games} THEN ROUND(SUM(pms.goals + pms.assists)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) ELSE NULL END AS ga_ratio

        FROM player_match_stats pms
        JOIN players pl ON pms.player_id = pl.id
        JOIN match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
        JOIN matches m ON pms.match_id = m.id
        WHERE pl.is_active = true
            {aside_condition}
        GROUP BY pl.id, pl.name
        HAVING COUNT(pms.match_id) > 0
        ORDER BY {col1} {dir1} NULLS LAST;
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
        print(f"Error in /api/player-gaos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/player-partnership')
def api_player_partnership():
    aside = request.args.get('aside', 'all')
    group_size = int(request.args.get('size', 2))
    target_player = request.args.get('player', '')
    sort_by = request.args.get('sort', 'win_pct')  # 💡 接收排序欄位，預設為 win_pct
    
    min_games = 3 if aside == '7' else 6
    aside_cond = f"AND m.pitch_aside = {int(aside)}" if aside in ['7', '9'] else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = f"""
        SELECT 
            m.id AS match_id,
            mt.team_color,
            mt.result,
            p.name AS player_name
        FROM matches m
        JOIN match_teams mt ON m.id = mt.match_id
        JOIN player_match_stats pms ON m.id = pms.match_id AND mt.team_color = pms.team_color
        JOIN players p ON pms.player_id = p.id
        WHERE mt.result IN ('Win', 'Draw', 'Lose')
        {aside_cond}
        ORDER BY m.match_date, m.id, mt.team_color, p.name;
    """
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    match_teams_dict = {}
    for row in rows:
        if isinstance(row, dict):
            match_id = row.get('match_id')
            team_color = row.get('team_color')
            result = row.get('result')
            player_name = row.get('player_name')
        else:
            match_id, team_color, result, player_name = row[0], row[1], row[2], row[3]

        key = (match_id, team_color)
        if key not in match_teams_dict:
            match_teams_dict[key] = {'result': result, 'players': []}
        
        if player_name not in match_teams_dict[key]['players']:
            match_teams_dict[key]['players'].append(player_name)

    stats = {}

    for key, data in match_teams_dict.items():
        team_players = sorted(data['players'])
        result = data['result']

        if len(team_players) >= group_size:
            for combo in combinations(team_players, group_size):
                if target_player and target_player not in combo:
                    continue
                
                part_name = " + ".join(combo)

                if part_name not in stats:
                    stats[part_name] = {'games': 0, 'wins': 0, 'draws': 0, 'losses': 0}

                stats[part_name]['games'] += 1
                if result == 'Win':
                    stats[part_name]['wins'] += 1
                elif result == 'Draw':
                    stats[part_name]['draws'] += 1
                elif result == 'Lose':
                    stats[part_name]['losses'] += 1

    results = []
    for part_name, data in stats.items():
        games = data['games']
        if games < min_games:
            continue

        wins = data['wins']
        draws = data['draws']
        losses = data['losses']

        win_pct = (wins / games) * 100 if games > 0 else 0
        unbeaten_pct = ((wins + draws) / games) * 100 if games > 0 else 0

        results.append({
            'partnership': part_name,
            'games': games,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_pct': round(win_pct, 2),
            'unbeaten_pct': round(unbeaten_pct, 2)
        })

# 💡 根據 User 選擇的欄位與邏輯進行精準排序
    # 針對不同的欄位設定正確的升冪(False)或降冪(True)
    reverse_flag = True  # 預設由大到小 (High -> Low)
    
# 💡 確保完全只依照使用者選定的單一欄位由大到小 (DESC) 排序
    # 當數值日時，不再有多餘的次要條件去干擾順序
    sort_key_map = {
        'win_pct': 'win_pct',
        'unbeaten_pct': 'unbeaten_pct',
        'games': 'games',
        'wins': 'wins',
        'draws': 'draws',
        'losses': 'losses'
    }
    
    target_sort_field = sort_key_map.get(sort_by, 'win_pct')
    
    # 單純以選定的欄位數值進行降冪排序 (High -> Low)
    results.sort(key=lambda x: x.get(target_sort_field, 0), reverse=True)

    return jsonify(results)

@app.route('/api/active-players')
def api_active_players():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 💡 從資料庫查詢所有 is_active = true 的球員並依名字排序
        cursor.execute("SELECT id, name FROM players WHERE is_active = true ORDER BY name ASC;")
        players = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(players)
    except Exception as e:
        print(f"Error in /api/active-players: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)