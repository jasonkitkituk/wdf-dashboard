import streamlit as st
import pandas as pd
import psycopg2

# 1. 網頁基本設定
st.set_page_config(page_title="足球隊數據分析中心", layout="wide")
st.title("⚽ 足球隊綜合統計與分析工具")

# 2. 連接 Supabase 資料庫
@st.cache_resource
def get_connection():
    # 從 .streamlit/secrets.toml 讀取連線字串
    return psycopg2.connect(st.secrets["postgres_url"])

# 3. 側邊欄控制項 (賽制選擇)
st.sidebar.header("⚙️ 篩選設定")
match_mode = st.sidebar.radio(
    "選擇賽制模式：",
    ("OVERALL", "7ASIDE", "9SIDE")
)

# 4. 載入資料按鈕
if st.sidebar.button("載入/更新數據"):
    conn = get_connection()
    
    # 這裡放我們之前寫好的 SQL（加入變數控制）
    query = f"""
    WITH match_mode AS (
        SELECT '{match_mode}' AS mode 
    ),
    team_inputs AS (
        SELECT 'TEAM_1' AS team_name, unnest(ARRAY['KenL','Michael','MikeL','JackLau','Jason','KitY','Chris','Sunny','Bill', 'Raymond']) AS player_name
        UNION ALL
        SELECT 'TEAM_2', unnest(ARRAY['Dom','Kolo Wai', 'Jimmy', 'KaKi', 'Kan', 'YingKit', 'Kenji', 'Roy', 'Henry'])
    ),
    base_match_data AS (
        SELECT 
            ti.team_name, p.id AS player_id, p.name AS player_name,
            pms.match_id, LOWER(TRIM(pms.team_color)) AS team_color,
            COALESCE(pms.goals, 0) AS goals, COALESCE(pms.assists, 0) AS assists,
            UPPER(TRIM(mt.result)) AS result
        FROM team_inputs ti
        JOIN public.players p ON LOWER(TRIM(p.name)) = LOWER(TRIM(ti.player_name))
        JOIN public.player_match_stats pms ON p.id = pms.player_id
        JOIN public.match_teams mt ON pms.match_id = mt.match_id AND LOWER(TRIM(pms.team_color)) = LOWER(TRIM(mt.team_color))
        JOIN public.matches m ON pms.match_id = m.id
        CROSS JOIN match_mode mm
        WHERE mm.mode = 'OVERALL' OR (mm.mode = '7ASIDE' AND m.pitch_aside = 7) OR (mm.mode = '9SIDE' AND m.pitch_aside = 9)
    ),
    player_summary AS (
        SELECT 
            team_name, player_id, player_name,
            COUNT(DISTINCT match_id) AS total_matches,
            SUM(goals) AS total_goals, SUM(assists) AS total_assists,
            (SUM(CASE WHEN result IN ('WIN', 'W', '勝') THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(DISTINCT match_id), 0)) AS win_rate
        FROM base_match_data
        GROUP BY team_name, player_id, player_name
    ),
    team_single_metrics AS (
        SELECT 
            t.team_name,
            COALESCE(SUM(ps.total_goals)::TEXT, '0') AS m1,
            COALESCE((SELECT player_name || ' (' || total_goals || ')' FROM player_summary ps2 WHERE ps2.team_name = t.team_name ORDER BY total_goals DESC, player_name LIMIT 1), 'N/A') AS m2,
            COALESCE((SELECT player_name || ' (' || total_assists || ')' FROM player_summary ps2 WHERE ps2.team_name = t.team_name ORDER BY total_assists DESC, player_name LIMIT 1), 'N/A') AS m3
        FROM (SELECT DISTINCT team_name FROM team_inputs) t
        LEFT JOIN player_summary ps ON t.team_name = ps.team_name
        GROUP BY t.team_name
    ),
    report_rows AS (
        SELECT 1 AS row_id, '總入球' AS metric_name, team_name, m1 AS val FROM team_single_metrics
        UNION ALL SELECT 2, 'Top Scorer', team_name, m2 FROM team_single_metrics
        UNION ALL SELECT 3, 'Most Assist', team_name, m3 FROM team_single_metrics
    )
    SELECT 
        rr.metric_name AS "分析項目",
        MAX(CASE WHEN rr.team_name = 'TEAM_1' THEN rr.val END) AS "TEAM_1",
        MAX(CASE WHEN rr.team_name = 'TEAM_2' THEN rr.val END) AS "TEAM_2"
    FROM report_rows rr
    GROUP BY rr.row_id, rr.metric_name
    ORDER BY rr.row_id;
    """
    
    df = pd.read_sql(query, conn)
    st.success(f"成功載入模式：{match_mode}")
    st.dataframe(df, use_container_width=True)
else:
    st.info("請點擊左側的「載入/更新數據」按鈕來生成報表。")