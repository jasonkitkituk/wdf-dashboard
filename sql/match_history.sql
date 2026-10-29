-- sql/match_history.sql
WITH match_teams_agg AS (
    SELECT 
        mt.match_id,
        mt.team_color,
        mt.result,
        SUM(COALESCE(pms.goals, 0)) AS team_goals, -- 💡 改用加總計算該隊總進球數
        json_agg(
            json_build_object(
                'player_id', p.id,
                'player_name', p.name,
                'goals', COALESCE(pms.goals, 0),
                'assists', COALESCE(pms.assists, 0),
                'own_goals', COALESCE(pms.own_goals, 0)
            ) ORDER BY pms.goals DESC, pms.assists DESC, p.name
        ) AS players
    FROM public.match_teams mt
    JOIN public.player_match_stats pms ON mt.match_id = pms.match_id AND mt.team_color = pms.team_color
    JOIN public.players p ON pms.player_id = p.id
    GROUP BY mt.match_id, mt.team_color, mt.result
)
SELECT 
    m.id AS match_id,
    TO_CHAR(m.match_date, 'YYYY-MM-DD') AS match_date,
    COALESCE(l.name, 'N/A') AS location,
    m.pitch_aside,
    json_agg(
        json_build_object(
            'team_color', mta.team_color,
            'goals', mta.team_goals,
            'result', mta.result,
            'players', mta.players
        ) ORDER BY CASE WHEN LOWER(mta.team_color) = 'red' THEN 1 ELSE 2 END
    ) AS teams
FROM public.matches m
LEFT JOIN public.locations l ON m.location_id = l.id
JOIN match_teams_agg mta ON m.id = mta.match_id
GROUP BY m.id, m.match_date, l.name, m.pitch_aside
ORDER BY m.match_date DESC, m.id DESC;