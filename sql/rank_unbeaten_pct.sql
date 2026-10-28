-- sql/rank_unbeaten_pct.sql
WITH player_unbeaten_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        -- 從 match_teams 表格中透過 match_id 與 team_color 判斷勝負與和局
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END) AS draws,
        COUNT(pms.match_id) AS appearances
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    -- 關鍵：關聯 match_teams 以取得該場該隊的比賽結果
    JOIN match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    HAVING COUNT(pms.match_id) >= %s
)
SELECT 
    ROW_NUMBER() OVER (
        ORDER BY ((p.wins + p.draws)::NUMERIC / NULLIF(p.appearances, 0)) DESC, 
                 (p.wins + p.draws) DESC, 
                 p.wins DESC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.wins,
    p.draws,
    p.appearances,
    ROUND(((p.wins + p.draws)::NUMERIC / NULLIF(p.appearances, 0)) * 100, 2) AS unbeaten_pct
FROM player_unbeaten_stats p
ORDER BY unbeaten_pct DESC, (p.wins + p.draws) DESC, p.wins DESC, p.player_name ASC
LIMIT 10;