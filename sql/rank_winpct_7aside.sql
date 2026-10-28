-- Appearances >= 3 --

SELECT 
    ROW_NUMBER() OVER (ORDER BY (SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) DESC, SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) DESC) as rank,
    pl.name AS player_name,
    ROUND((SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) AS win_pct,
    COUNT(pms.match_id) AS appearances
FROM 
    player_match_stats pms
JOIN 
    players pl ON pms.player_id = pl.id
JOIN 
    match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
JOIN 
    matches m ON pms.match_id = m.id
WHERE 
    m.pitch_aside = 7 
    AND pl.is_active = true
GROUP BY 
    pl.id, pl.name
HAVING 
    COUNT(pms.match_id) >= 3
ORDER BY 
    win_pct DESC, 
    appearances DESC
LIMIT 10;