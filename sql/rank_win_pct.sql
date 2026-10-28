-- sql/rank_win_pct.sql
WITH player_win_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins,
        COUNT(pms.match_id) AS appearances
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    JOIN match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    HAVING COUNT(pms.match_id) >= %s
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY (p.wins::NUMERIC / NULLIF(p.appearances, 0)) DESC, p.wins DESC, p.player_name ASC) AS rank,
    p.player_name,
    p.wins,
    p.appearances,
    ROUND((p.wins::NUMERIC / NULLIF(p.appearances, 0)) * 100, 2) AS win_pct
FROM player_win_stats p
ORDER BY win_pct DESC, p.wins DESC, p.player_name ASC
LIMIT 10;