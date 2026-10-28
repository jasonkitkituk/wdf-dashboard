-- sql/lmf_stats.sql
WITH player_match_history AS (
    -- 為每個球員找出他自己參與過的所有比賽，並依時間倒序編號 (rn = 1 代表該球員最近的一場)
    SELECT 
        p.id AS player_id,
        p.name AS player_name,
        mt.result,
        ROW_NUMBER() OVER (PARTITION BY p.id ORDER BY m.match_date DESC, m.id DESC) AS rn
    FROM players p
    JOIN player_match_stats pms ON p.id = pms.player_id
    JOIN matches m ON pms.match_id = m.id
    JOIN match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    WHERE p.is_active = true
),
player_recent_6 AS (
    -- 只取每個球員最近參與的 1 到 6 場
    SELECT 
        player_id,
        player_name,
        rn,
        result,
        CASE 
            WHEN result = 'Win' THEN 3
            WHEN result = 'Draw' THEN 1
            WHEN result = 'Lose' THEN 0
            ELSE 0
        END AS score_weight,
        CASE 
            WHEN result = 'Win' THEN 3
            WHEN result = 'Draw' THEN 1
            WHEN result = 'Lose' THEN 0
            ELSE 0
        END AS sort_weight
    FROM player_match_history
    WHERE rn <= 6
),
player_pivot AS (
    -- 轉置成 6 個欄位
    SELECT 
        player_id,
        player_name,
        MAX(CASE WHEN rn = 6 THEN result END) AS m6,
        MAX(CASE WHEN rn = 5 THEN result END) AS m5,
        MAX(CASE WHEN rn = 4 THEN result END) AS m4,
        MAX(CASE WHEN rn = 3 THEN result END) AS m3,
        MAX(CASE WHEN rn = 2 THEN result END) AS m2,
        MAX(CASE WHEN rn = 1 THEN result END) AS m1, -- 最近一場在 m1 (對應最右邊)
        
        MAX(CASE WHEN rn = 6 THEN sort_weight ELSE 0 END) AS w6,
        MAX(CASE WHEN rn = 5 THEN sort_weight ELSE 0 END) AS w5,
        MAX(CASE WHEN rn = 4 THEN sort_weight ELSE 0 END) AS w4,
        MAX(CASE WHEN rn = 3 THEN sort_weight ELSE 0 END) AS w3,
        MAX(CASE WHEN rn = 2 THEN sort_weight ELSE 0 END) AS w2,
        MAX(CASE WHEN rn = 1 THEN sort_weight ELSE 0 END) AS w1,

        SUM(score_weight) AS total_points,
        COUNT(result) AS appearances
    FROM player_recent_6
    GROUP BY player_id, player_name
    HAVING COUNT(result) >= 6 -- 嚴格要求必須至少有 6 場出場紀錄
)
SELECT 
    player_id,
    player_name,
    m6, m5, m4, m3, m2, m1, -- 顯示時由左至右為：較早 ➔ 最近 (m1 在最右)
    total_points,
    w1, w2, w3, w4, w5, w6,
    appearances
FROM player_pivot
ORDER BY 
    total_points DESC,
    w1 DESC, m1 DESC,
    w2 DESC, m2 DESC,
    w3 DESC, m3 DESC,
    w4 DESC, m4 DESC,
    w5 DESC, m5 DESC,
    w6 DESC, m6 DESC,
    player_name ASC;