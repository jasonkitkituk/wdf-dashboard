from flask import Blueprint, jsonify, request
from itertools import combinations
import psycopg2
import psycopg2.extras
import os

part_bp = Blueprint('part_bp', __name__)

def get_db_connection():
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:www.WDF123.com@db.pdmcmmibyyjjelwmcgjs.supabase.co:5432/postgres"
    )
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@part_bp.route('/api/player-partnership')
def api_player_partnership():
    # ... 原本 api_player_partnership 的程式碼 ...
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
    

@part_bp.route('/api/active-players')
def api_active_players():
    # ... 原本 api_active_players 的程式碼 ...
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
    