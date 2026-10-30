# routes/lmf_routes.py
from flask import Blueprint, jsonify
import os
import psycopg2
import psycopg2.extras
from routes.db import get_db_connection

lmf_bp = Blueprint('lmf_bp', __name__)



def load_sql_query(filename):
    path = os.path.join('sql', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

@lmf_bp.route('/api/lmf-stats')
def api_lmf_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = load_sql_query('lmf_stats.sql')
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": rows})
    except Exception as e:
        print(f"Error in /api/lmf-stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500