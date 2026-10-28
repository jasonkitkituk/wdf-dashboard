-- sql/lmf_stats.sql
WITH recent_6_matches AS (
    -- 取得最新的 6 場比賽，並標記序號 (1 代表最近的一場)
    SELECT id, match_date, 
           ROW_NUMBER() OVER (ORDER BY match_date DESC, id DESC) AS match_rank
    FROM matches
    ORDER BY match_date DESC, id DESC
    LIMIT 6
),
player_recent_results AS (
    -- 找出所有活躍球員在最近 6 場比賽中的成績
    SELECT 
        p.id AS player_id,
        p.name AS player_name,
        rm.match_rank,
        mt.result,
        CASE 
            WHEN mt.result = 'Win' THEN 3
            WHEN mt.result = 'Draw' THEN 1
            WHEN mt.result = 'Lose' THEN 0
            ELSE 0 -- 沒有參與記作 0 分
        END AS score_weight,
        -- 用於排序權重：有參與(Win/Draw/Lose)大於沒有參與(NULL)
        CASE 
            WHEN mt.result = 'Win' THEN 3
            WHEN mt.result = 'Draw' THEN 1
            WHEN mt.result = 'Lose' THEN 0
            ELSE -1 -- 用作排序時讓沒有參與排在後面
        END AS sort_weight
    FROM players p
    CROSS JOIN recent_6_matches rm
    LEFT JOIN player_match_stats pms 
        ON p.id = pms.player_id AND rm.id = pms.match_id
    LEFT JOIN match_teams mt 
        ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    WHERE p.is_active = true
),
player_pivot AS (
    -- 轉置為 6 個比賽欄位，並計算總分與排序權重
    SELECT 
        player_id,
        player_name,
        MAX(CASE WHEN match_rank = 1 THEN result END) AS m1,
        MAX(CASE WHEN match_rank = 2 THEN result END) AS m2,
        MAX(CASE WHEN match_rank = 3 THEN result END) AS m3,
        MAX(CASE WHEN match_rank = 4 THEN result END) AS m4,
        MAX(CASE WHEN match_rank = 5 THEN result END) AS m5,
        MAX(CASE WHEN match_rank = 6 THEN result END) AS m6,
        
        MAX(CASE WHEN match_rank = 1 THEN sort_weight ELSE -2 END) AS w1,
        MAX(CASE WHEN match_rank = 2 THEN sort_weight ELSE -2 END) AS w2,
        MAX(CASE WHEN match_rank = 3 THEN sort_weight ELSE -2 END) AS w3,
        MAX(CASE WHEN match_rank = 4 THEN sort_weight ELSE -2 END) AS w4,
        MAX(CASE WHEN match_rank = 5 THEN sort_weight ELSE -2 END) AS w5,
        MAX(CASE WHEN match_rank = 6 THEN sort_weight ELSE -2 END) AS w6,

        SUM(CASE WHEN score_weight >= 0 THEN score_weight ELSE 0 END) AS total_points,
        COUNT(CASE WHEN result IS NOT NULL THEN 1 END) AS appearances
    FROM player_recent_results
    GROUP BY player_id, player_name
)
SELECT 
    player_id,
    player_name,
    m6, m5, m4, m3, m2, m1, -- 依照時間順序：左邊較早 (m6) -> 右邊最近 (m1)
    total_points,
    appearances
FROM player_pivot
ORDER BY 
    total_points DESC,
    w1 DESC, -- 最近第 1 場結果
    w2 DESC, -- 最近第 2 場結果
    w3 DESC, 
    w4 DESC, 
    w5 DESC, 
    w6 DESC, 
    player_name ASC;