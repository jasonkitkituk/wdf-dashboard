SELECT 
    pl.id AS player_id,
    pl.name AS player_name,
    SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END) AS win,
    SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END) AS draw,
    SUM(CASE WHEN mt.result = 'Lose' THEN 1 ELSE 0 END) AS lose,
    COUNT(pms.match_id) AS total,
    SUM(CASE WHEN mt.result IN ('Win', 'Draw') THEN 1 ELSE 0 END) AS unbeaten,
    SUM(CASE 
        WHEN mt.result = 'Win' THEN 3 
        WHEN mt.result = 'Draw' THEN 1 
        ELSE 0 
    END) AS point,
    
    -- 僅 >= 6 場才計算的欄位
    CASE WHEN COUNT(pms.match_id) >= 6 THEN ROUND(SUM(CASE WHEN mt.result = 'Win' THEN 3 WHEN mt.result = 'Draw' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0), 2) ELSE NULL END AS avg_point,
    CASE WHEN COUNT(pms.match_id) >= 6 THEN ROUND((SUM(CASE WHEN mt.result = 'Win' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS win_pct,
    CASE WHEN COUNT(pms.match_id) >= 6 THEN ROUND((SUM(CASE WHEN mt.result = 'Draw' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS draw_pct,
    CASE WHEN COUNT(pms.match_id) >= 6 THEN ROUND((SUM(CASE WHEN mt.result = 'Lose' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS lose_pct,
    CASE WHEN COUNT(pms.match_id) >= 6 THEN ROUND((SUM(CASE WHEN mt.result IN ('Win', 'Draw') THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(pms.match_id), 0)) * 100, 2) ELSE NULL END AS unbeaten_pct

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
    -- 💡 核心：透過傳入的 aside 參數決定篩選條件 (如果是 'all' 則不限)
    AND (:aside = 'all' OR m.pitch_aside = :aside::integer)
GROUP BY 
    pl.id, pl.name
HAVING 
    COUNT(pms.match_id) > 0
-- 💡 支援動態排序與第二、第三順位排序（防範 SQL Injection，後端會做白名單校驗）
ORDER BY 
    {sort_col_1} {sort_dir_1},
    {sort_col_2} {sort_dir_2},
    {sort_col_3} {sort_dir_3};