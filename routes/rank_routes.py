# routes/rank_routes.py
from flask import Blueprint, jsonify
import psycopg2
import psycopg2.extras
import os

rank_bp = Blueprint('rank_bp', __name__)

def get_db_connection():
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:www.WDF123.com@db.pdmcmmibyyjjelwmcgjs.supabase.co:5432/postgres"
    )
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def load_sql_query(filename):
    path = os.path.join('sql', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@rank_bp.route('/api/rank-goals-all')
def api_rank_goals_all():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('rank_goals.sql')

        # 1. Overall (pitch_aside = None, 最少 6 場)
        cursor.execute(sql_query, (None, None, 6))
        rank_overall = cursor.fetchall()

        # 2. 9-a-side (pitch_aside = 9, 最少 6場)
        cursor.execute(sql_query, (9, 9, 6))
        rank_9side = cursor.fetchall()

        # 3. 7-a-side (pitch_aside = 7, 最少 3 場)
        cursor.execute(sql_query, (7, 7, 3))
        rank_7side = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "overall": rank_overall,
            "nine_side": rank_9side,
            "seven_side": rank_7side
        })
    except Exception as e:
        print(f"Error in /api/rank-goals-all: {e}")
        return jsonify({"error": str(e)}), 500

    
@rank_bp.route('/api/rank-winpct-all')
def api_rank_winpct_all():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('rank_win_pct.sql')

        # 1. Overall Win% (pitch_aside = None, 最少 6 場)
        cursor.execute(sql_query, (None, None, 6))
        winpct_overall = cursor.fetchall()

        # 2. 9-a-side Win% (pitch_aside = 9, 最少 6 場)
        cursor.execute(sql_query, (9, 9, 6))
        winpct_9side = cursor.fetchall()

        # 3. 7-a-side Win% (pitch_aside = 7, 最少 3 場)
        cursor.execute(sql_query, (7, 7, 3))
        winpct_7side = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "overall": winpct_overall,
            "nine_side": winpct_9side,
            "seven_side": winpct_7side
        })
    except Exception as e:
        print(f"Error in /api/rank-winpct-all: {e}")
        return jsonify({"error": str(e)}), 500

@rank_bp.route('/api/rank-goalpct-all')
def api_rank_goalpct_all():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('rank_goal_pct.sql')

        # 1. Overall Goal% (pitch_aside = None, 最少 6 場)
        cursor.execute(sql_query, (None, None, 6))
        goalpct_overall = cursor.fetchall()

        # 2. 9-a-side Goal% (pitch_aside = 9, 最少 6 場)
        cursor.execute(sql_query, (9, 9, 6))
        goalpct_9side = cursor.fetchall()

        # 3. 7-a-side Goal% (pitch_aside = 7, 最少 3 場)
        cursor.execute(sql_query, (7, 7, 3))
        goalpct_7side = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "overall": goalpct_overall,
            "nine_side": goalpct_9side,
            "seven_side": goalpct_7side
        })
    except Exception as e:
        print(f"Error in /api/rank-goalpct-all: {e}")
        return jsonify({"error": str(e)}), 500


@rank_bp.route('/api/rank-unbeatenpct-all')
def api_rank_unbeatenpct_all():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('rank_unbeaten_pct.sql')

        # 1. Overall Unbeaten% (pitch_aside = None, 最少 6 場)
        cursor.execute(sql_query, (None, None, 6))
        unbeatenpct_overall = cursor.fetchall()

        # 2. 9-a-side Unbeaten% (pitch_aside = 9, 最少 6 場)
        cursor.execute(sql_query, (9, 9, 6))
        unbeatenpct_9side = cursor.fetchall()

        # 3. 7-a-side Unbeaten% (pitch_aside = 7, 最少 3 場)
        cursor.execute(sql_query, (7, 7, 3))
        unbeatenpct_7side = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "overall": unbeatenpct_overall,
            "nine_side": unbeatenpct_9side,
            "seven_side": unbeatenpct_7side
        })
    except Exception as e:
        print(f"Error in /api/rank-unbeatenpct-all: {e}")
        return jsonify({"error": str(e)}), 500