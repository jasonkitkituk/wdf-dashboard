-- sql/rank_assist_pct.sql
WITH player_assist_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(pms.assists) AS total_assists,
        COUNT(pms.match_id) AS appearances
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    HAVING COUNT(pms.match_id) >= %s
)
SELECT 
    ROW_NUMBER() OVER (
        ORDER BY (p.total_assists::NUMERIC / NULLIF(p.appearances, 0)) DESC, 
                 p.total_assists DESC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.total_assists AS assists,
    p.appearances,
    ROUND((p.total_assists::NUMERIC / NULLIF(p.appearances, 0)), 2) AS assist_pct
FROM player_assist_stats p
ORDER BY assist_pct DESC, p.total_assists DESC, p.player_name ASC
LIMIT 10;