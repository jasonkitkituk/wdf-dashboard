from flask import Blueprint, jsonify, request
from itertools import combinations
import psycopg2
import psycopg2.extras
import os
from routes.db import get_db_connection

part_bp = Blueprint('part_bp', __name__)



from flask import Blueprint, jsonify, request
from itertools import combinations
import psycopg2
import psycopg2.extras
import os
from routes.db import get_db_connection

part_bp = Blueprint('part_bp', __name__)

@part_bp.route('/api/player-partnership')
def api_player_partnership():
    aside = request.args.get('aside', 'all')
    group_size = int(request.args.get('size', 2))
    target_player = request.args.get('player', '')
    sort_by = request.args.get('sort', 'win_pct')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 💡 1. 動態從 DB 查詢當前 group_size 對應的 Threshold (min_games)
    cursor.execute("SELECT min_games FROM combo_thresholds WHERE group_size = %s;", (group_size,))
    threshold_row = cursor.fetchone()
    
    #print(f"DEBUG: group_size = {group_size}, threshold_row from DB = {threshold_row}")  # 👈 加上這行看終端機輸出

    if threshold_row:
        # 支援 fetchall/fetchone 返回 dict 或 tuple 的處理
        min_games = threshold_row['min_games'] if isinstance(threshold_row, dict) else threshold_row[0]
    else:
        # Fallback 預設備用機制
        default_thresholds = {2: 6, 3: 5, 4: 4, 5: 3, 6: 3, 7: 3}
        min_games = default_thresholds.get(group_size, 6)

    # 💡 如果選擇的是 7-a-side，可視需求保持減半或使用獨立邏輯 (此處為原生 aside 條件)
    aside_cond = f"AND m.pitch_aside = {int(aside)}" if aside in ['7', '9'] else ""

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
        
        # 💡 使用從 DB 動態讀取的 min_games 過濾
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

    sort_key_map = {
        'win_pct': 'win_pct',
        'unbeaten_pct': 'unbeaten_pct',
        'games': 'games',
        'wins': 'wins',
        'draws': 'draws',
        'losses': 'losses'
    }
    
    target_sort_field = sort_key_map.get(sort_by, 'win_pct')
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


@part_bp.route('/api/combo-thresholds')
def api_combo_thresholds():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 按照 group_size 順序排好
        cursor.execute("SELECT group_size, min_games FROM combo_thresholds ORDER BY group_size ASC;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # 整理成方便前端讀取的格式
        thresholds = []
        for row in rows:
            if isinstance(row, dict):
                thresholds.append({"size": row.get("group_size"), "threshold": row.get("min_games")})
            else:
                thresholds.append({"size": row[0], "threshold": row[1]})

        return jsonify(thresholds)
    except Exception as e:
        print(f"Error in /api/combo-thresholds: {e}")
        return jsonify({"error": str(e)}), 500