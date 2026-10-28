-- sql/rank_assist.sql
WITH player_assist_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(pms.assists) AS total_assists,
        COUNT(pms.match_id) AS appearances,
        ROUND(SUM(pms.assists)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) AS assist_pct
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
        ORDER BY p.total_assists DESC, 
                 p.assist_pct DESC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.total_assists AS assists,
    p.appearances,
    p.assist_pct
FROM player_assist_stats p
ORDER BY assists DESC, assist_pct DESC, p.player_name ASC
LIMIT 10;