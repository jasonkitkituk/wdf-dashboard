# routes/wld_routes.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import os
from routes.db import get_db_connection

# 建立 WLD 專屬藍圖
wld_bp = Blueprint('wld_bp', __name__)



@wld_bp.route('/api/player-wld')
def api_player_wld():
    aside = request.args.get('aside', 'all')
    sort1 = request.args.get('sort1', 'point:desc')
    days = request.args.get('days', 'all')  # 💡 接收時間篩選參數 (all, 30, 60, 90)

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
            {date_condition}
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