SELECT DISTINCT TO_CHAR(match_date, 'YYYY-MM-DD') AS match_date
FROM public.matches
WHERE match_date IS NOT NULL
ORDER BY match_date DESC;