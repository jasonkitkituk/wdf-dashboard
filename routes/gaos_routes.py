# routes/gaos_routes.py
import psycopg2
import psycopg2.extras
import os
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from routes.db import get_db_connection

# 建立 GAOS 專屬藍圖
gaos_bp = Blueprint('gaos_bp', __name__)



@gaos_bp.route('/api/player-gaos')
def api_player_gaos():
    aside = request.args.get('aside', 'all')
    sort1 = request.args.get('sort1', 'player_name:asc')
    days = request.args.get('days', 'all')  # 💡 接收時間篩選參數 (all, 30, 60, 90)

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

    # 💡 處理時間條件篩選
    date_condition = ""
    if days in ['30', '60', '90']:
        limit_date = datetime.now().date() - timedelta(days=int(days))
        date_condition = "AND m.match_date >= %s"
        query_params.append(limit_date)

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
            {date_condition}
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
