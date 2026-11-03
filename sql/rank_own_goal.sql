-- sql/rank_own_goal.sql 臨時測試版
WITH player_owngoal_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(pms.own_goals) AS own_goals,
        COUNT(pms.match_id) AS appearances
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    -- 💡 暫時拿掉 HAVING 限制，讓所有活躍球員都跑出來
)
SELECT 
    ROW_NUMBER() OVER (
        ORDER BY p.own_goals DESC, 
                 p.appearances ASC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.own_goals,
    p.appearances
FROM player_owngoal_stats p
ORDER BY own_goals DESC, appearances ASC, p.player_name ASC
LIMIT 10;