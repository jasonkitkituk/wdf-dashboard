-- sql/rank_ga.sql
WITH player_ga_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(pms.goals + pms.assists) AS total_ga,
        COUNT(pms.match_id) AS appearances,
        ROUND(SUM(pms.goals + pms.assists)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) AS ga_pct
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
        ORDER BY p.total_ga DESC, 
                 p.ga_pct DESC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.total_ga AS ga,
    p.appearances,
    p.ga_pct
FROM player_ga_stats p
ORDER BY ga DESC, ga_pct DESC, p.player_name ASC
LIMIT 10;