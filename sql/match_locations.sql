SELECT DISTINCT l.name AS location
FROM public.matches m
JOIN public.locations l ON m.location_id = l.id
WHERE l.name IS NOT NULL AND l.name != ''
ORDER BY l.name ASC;