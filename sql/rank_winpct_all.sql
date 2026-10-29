WITH player_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        -- Overall 數據
        SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins_overall,
        COUNT(pms.match_id) AS apps_overall,
        -- 9-a-side 數據
        SUM(CASE WHEN mt.result = 'Win' AND m.pitch_aside = 9 THEN 1 ELSE 0 END) AS wins_9side,
        COUNT(CASE WHEN m.pitch_aside = 9 THEN pms.match_id END) AS apps_9side,
        -- 7-a-side 數據
        SUM(CASE WHEN mt.result = 'Win' AND m.pitch_aside = 7 THEN 1 ELSE 0 END) AS wins_7side,
        COUNT(CASE WHEN m.pitch_aside = 7 THEN pms.match_id END) AS apps_7side
    FROM 
        player_match_stats pms
    JOIN 
        players pl ON pms.player_id = pl.id
    JOIN 
        match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
    JOIN 
        matches m ON pms.match_id = m.id
    WHERE 
        pl.is_active = true
    GROUP BY 
        pl.id, pl.name
),
rank_overall AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY (wins_overall::NUMERIC / NULLIF(apps_overall, 0)) DESC, wins_overall DESC) AS rank,
        player_name,
        ROUND((wins_overall::NUMERIC / NULLIF(apps_overall, 0)) * 100, 2) AS win_pct,
        apps_overall AS appearances
    FROM player_stats
    WHERE apps_overall >= 6
    ORDER BY win_pct DESC, appearances DESC
    LIMIT 10
),
rank_9side AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY (wins_9side::NUMERIC / NULLIF(apps_9side, 0)) DESC, wins_9side DESC) AS rank,
        player_name,
        ROUND((wins_9side::NUMERIC / NULLIF(apps_9side, 0)) * 100, 2) AS win_pct,
        apps_9side AS appearances
    FROM player_stats
    WHERE apps_9side >= 6
    ORDER BY win_pct DESC, appearances DESC
    LIMIT 10
),
rank_7side AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY (wins_7side::NUMERIC / NULLIF(apps_7side, 0)) DESC, wins_7side DESC) AS rank,
        player_name,
        ROUND((wins_7side::NUMERIC / NULLIF(apps_7side, 0)) * 100, 2) AS win_pct,
        apps_7side AS appearances
    FROM player_stats
    WHERE apps_7side >= 3
    ORDER BY win_pct DESC, appearances DESC
    LIMIT 10
)
SELECT 
    (SELECT json_agg(r) FROM rank_overall r) AS overall,
    (SELECT json_agg(r) FROM rank_9side r) AS nine_side,
    (SELECT json_agg(r) FROM rank_7side r) AS seven_side;