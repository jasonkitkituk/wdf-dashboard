SELECT id, name
FROM public.players
WHERE is_active = true
ORDER BY name ASC;