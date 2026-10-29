-- sql/match_history.sql
WITH match_teams_basic AS (
    -- 1. 先抓出每隊基本資料與對手失球數 (goals_conceded)
    SELECT 
        mt.match_id,
        mt.team_color,
        mt.result,
        mt.goals_conceded,
        -- 計算對手的失球數，即為本隊的總得分 (包含正規進球與對方烏龍球)
        COALESCE(
            SUM(mt.goals_conceded) OVER (PARTITION BY mt.match_id) - mt.goals_conceded, 
            0
        ) AS calculated_team_goals
    FROM public.match_teams mt
),
match_teams_agg AS (
    -- 2. 組合球員個人統計數據 JSON
    SELECT 
        tb.match_id,
        tb.team_color,
        tb.result,
        tb.calculated_team_goals AS team_goals,
        COALESCE(
            json_agg(
                json_build_object(
                    'player_id', p.id,
                    'player_name', p.name,
                    'goals', COALESCE(pms.goals, 0),
                    'assists', COALESCE(pms.assists, 0),
                    'own_goals', COALESCE(pms.own_goals, 0)
                ) ORDER BY pms.goals DESC, pms.assists DESC, p.name
            ) FILTER (WHERE p.id IS NOT NULL), 
            '[]'::json
        ) AS players
    FROM match_teams_basic tb
    LEFT JOIN public.player_match_stats pms 
        ON tb.match_id = pms.match_id AND tb.team_color = pms.team_color
    LEFT JOIN public.players p 
        ON pms.player_id = p.id
    GROUP BY tb.match_id, tb.team_color, tb.result, tb.calculated_team_goals
)
SELECT 
    m.id AS match_id,
    TO_CHAR(m.match_date, 'YYYY-MM-DD') AS match_date,
    COALESCE(l.name, 'N/A') AS location,
    m.pitch_aside,
    json_agg(
        json_build_object(
            'team_color', mta.team_color,
            'goals', COALESCE(mta.team_goals, 0),
            'result', mta.result,
            'players', mta.players
        ) ORDER BY CASE WHEN LOWER(mta.team_color) = 'red' THEN 1 ELSE 2 END
    ) AS teams
FROM public.matches m
LEFT JOIN public.locations l ON m.location_id = l.id
LEFT JOIN match_teams_agg mta ON m.id = mta.match_id
GROUP BY m.id, m.match_date, l.name, m.pitch_aside
ORDER BY m.match_date DESC, m.id DESC;