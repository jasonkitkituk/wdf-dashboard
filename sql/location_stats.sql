SELECT 
    l.name AS location_name,
    COUNT(CASE WHEN m.pitch_aside = 9 THEN 1 END) AS count_9aside,
    COUNT(CASE WHEN m.pitch_aside = 7 THEN 1 END) AS count_7aside,
    COUNT(m.id) AS overall_total
FROM 
    locations l
JOIN 
    matches m ON l.id = m.location_id
GROUP BY 
    l.id, l.name
HAVING 
    COUNT(m.id) > 0
ORDER BY 
    l.name ASC;