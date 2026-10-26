SELECT 
    ROW_NUMBER() OVER (ORDER BY SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) DESC, COUNT(pms.match_id) DESC) AS rank,
    p.name AS player_name,
    SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS wins,
    COUNT(pms.match_id) AS appearances
FROM public.players p
JOIN public.player_match_stats pms ON p.id = pms.player_id
JOIN public.match_teams mt ON pms.match_id = mt.match_id AND pms.team_color = mt.team_color
GROUP BY p.id, p.name
ORDER BY rank
LIMIT 10;