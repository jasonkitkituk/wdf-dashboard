-- sql/rank_gc_pct.sql
WITH player_gc_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(mt.goals_conceded) AS total_gc,
        COUNT(pms.match_id) AS appearances,
        ROUND(SUM(mt.goals_conceded)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) AS gc_pct
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
        ORDER BY p.gc_pct ASC,           -- 失球率越低越靠前
                 p.total_gc ASC,         -- 總失球越少越靠前
                 p.appearances DESC,     -- 出場次數越多越靠前
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.total_gc AS gc,
    p.appearances,
    p.gc_pct
FROM player_gc_stats p
ORDER BY gc_pct ASC, gc ASC, appearances DESC, p.player_name ASC
LIMIT 10;