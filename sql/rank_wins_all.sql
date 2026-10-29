WITH player_win_stats AS (
    SELECT 
        p.id AS player_id,
        p.name AS player_name,
        -- Overall
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins_overall,
        COUNT(pms.match_id) AS apps_overall,
        -- 9-a-side
        SUM(CASE WHEN mt.result = 'Win' AND m.pitch_aside = 9 THEN 1 ELSE 0 END) AS wins_9side,
        COUNT(CASE WHEN m.pitch_aside = 9 THEN pms.match_id END) AS apps_9side,
        -- 7-a-side
        SUM(CASE WHEN mt.result = 'Win' AND m.pitch_aside = 7 THEN 1 ELSE 0 END) AS wins_7side,
        COUNT(CASE WHEN m.pitch_aside = 7 THEN pms.match_id END) AS apps_7side
    FROM public.players p
    JOIN public.player_match_stats pms ON p.id = pms.player_id
    JOIN public.match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    JOIN public.matches m ON pms.match_id = m.id
    GROUP BY p.id, p.name
),
rank_overall AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY wins_overall DESC, apps_overall DESC) AS rank,
        player_name, wins_overall AS wins, apps_overall AS appearances
    FROM player_win_stats
    WHERE wins_overall > 0
    LIMIT 10
),
rank_9side AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY wins_9side DESC, apps_9side DESC) AS rank,
        player_name, wins_9side AS wins, apps_9side AS appearances
    FROM player_win_stats
    WHERE wins_9side > 0
    LIMIT 10
),
rank_7side AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY wins_7side DESC, apps_7side DESC) AS rank,
        player_name, wins_7side AS wins, apps_7side AS appearances
    FROM player_win_stats
    WHERE wins_7side > 0
    LIMIT 10
)
SELECT 
    (SELECT json_agg(r) FROM rank_overall r) AS overall,
    (SELECT json_agg(r) FROM rank_9side r) AS nine_side,
    (SELECT json_agg(r) FROM rank_7side r) AS seven_side;