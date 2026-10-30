import os
import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify
from routes.db import get_db_connection

match_bp = Blueprint('match_bp', __name__)




def load_sql_query(filename):
    path = os.path.join('sql', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@match_bp.route('/api/match-history')
def api_match_history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('match_history.sql')
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": rows})
    except Exception as e:
        print(f"Error in /api/match-history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# 💡 新增：提供前端動態下拉選單的選項資料
@match_bp.route('/api/match-filter-options')
def api_match_filter_options():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. 抓取日期
        cursor.execute(load_sql_query('match_dates.sql'))
        dates = [row['match_date'] for row in cursor.fetchall()]

        # 2. 抓取地點
        cursor.execute(load_sql_query('match_locations.sql'))
        locations = [row['location'] for row in cursor.fetchall()]

        # 3. 抓取 Active 球員
        cursor.execute(load_sql_query('active_players.sql'))
        players = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True, 
            "dates": dates,
            "locations": locations,
            "players": players
        })
    except Exception as e:
        print(f"Error in /api/match-filter-options: {e}")
        return jsonify({"success": False, "error": str(e)}), 500