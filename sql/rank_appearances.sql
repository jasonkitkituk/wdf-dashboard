-- sql/rank_appearances.sql
WITH player_app_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        COUNT(pms.match_id) AS appearances,
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins
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
    ROW_NUMBER() OVER (
        ORDER BY p.appearances DESC, 
                 p.wins DESC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.appearances,
    p.wins
FROM player_app_stats p
ORDER BY appearances DESC, wins DESC, p.player_name ASC
LIMIT 10;