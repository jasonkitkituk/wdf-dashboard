-- sql/rank_avg_point.sql
WITH player_stats AS (
    SELECT 
        p.id AS player_id,
        p.name AS player_name,
        COUNT(pms.match_id) AS appearances,
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END) AS draws,
        SUM(CASE WHEN mt.result = 'Lose' THEN 1 ELSE 0 END) AS losses,
        SUM(
            CASE 
                WHEN mt.result = 'Win' THEN 3 
                WHEN mt.result = 'Draw' THEN 1 
                ELSE 0 
            END
        ) AS total_points
    FROM public.players p
    JOIN public.player_match_stats pms ON p.id = pms.player_id
    JOIN public.matches m ON pms.match_id = m.id
    JOIN public.match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    WHERE p.is_active = TRUE
      AND (%s IS NULL OR m.pitch_aside = %s)
    GROUP BY p.id, p.name
    HAVING COUNT(pms.match_id) >= %s
),
ranked_players AS (
    SELECT 
        -- 💡 改用 ROW_NUMBER()，同分時以參與場數多 (appearances DESC) 優先，並嚴格編排 1~10 名
        ROW_NUMBER() OVER (
            ORDER BY 
                ROUND((total_points::numeric / appearances), 2) DESC,
                appearances DESC,
                wins DESC,
                player_name ASC
        ) AS rank,
        player_id,
        player_name,
        appearances,
        wins,
        draws,
        total_points,
        ROUND((total_points::numeric / appearances), 2) AS avg_point
    FROM player_stats
)
SELECT 
    rank,
    player_id,
    player_name,
    appearances,
    wins,
    draws,
    total_points,
    avg_point
FROM ranked_players
WHERE rank <= 10
ORDER BY rank ASC;