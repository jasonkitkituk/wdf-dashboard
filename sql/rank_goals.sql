-- sql/rank_goals.sql
WITH player_goal_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        SUM(COALESCE(pms.goals, 0)) AS goal,
        COUNT(pms.match_id) AS total_matches
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    HAVING COUNT(pms.match_id) >= %s
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY p.goal DESC, (p.goal::NUMERIC / NULLIF(p.total_matches, 0)) DESC, p.player_name ASC) AS rank,
    p.player_name,
    p.goal,
    ROUND(p.goal::NUMERIC / NULLIF(p.total_matches, 0), 2) AS goal_pct
FROM player_goal_stats p
ORDER BY p.goal DESC, goal_pct DESC, p.player_name ASC
LIMIT 10;