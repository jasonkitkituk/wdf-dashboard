SELECT 
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'black' AND LOWER(result) = 'win' THEN 1 ELSE 0 END), 0) as black_win,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'white' AND LOWER(result) = 'win' THEN 1 ELSE 0 END), 0) as white_win,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'blue' AND LOWER(result) = 'win' THEN 1 ELSE 0 END), 0) as blue_win,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'red' AND LOWER(result) = 'win' THEN 1 ELSE 0 END), 0) as red_win,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'green' AND LOWER(result) = 'win' THEN 1 ELSE 0 END), 0) as green_win,

    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'black' AND LOWER(result) = 'draw' THEN 1 ELSE 0 END), 0) as black_draw,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'white' AND LOWER(result) = 'draw' THEN 1 ELSE 0 END), 0) as white_draw,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'blue' AND LOWER(result) = 'draw' THEN 1 ELSE 0 END), 0) as blue_draw,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'red' AND LOWER(result) = 'draw' THEN 1 ELSE 0 END), 0) as red_draw,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'green' AND LOWER(result) = 'draw' THEN 1 ELSE 0 END), 0) as green_draw,

    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'black' AND LOWER(result) = 'lose' THEN 1 ELSE 0 END), 0) as black_lose,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'white' AND LOWER(result) = 'lose' THEN 1 ELSE 0 END), 0) as white_lose,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'blue' AND LOWER(result) = 'lose' THEN 1 ELSE 0 END), 0) as blue_lose,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'red' AND LOWER(result) = 'lose' THEN 1 ELSE 0 END), 0) as red_lose,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'green' AND LOWER(result) = 'lose' THEN 1 ELSE 0 END), 0) as green_lose,

    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'black' THEN 1 ELSE 0 END), 0) as black_total,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'white' THEN 1 ELSE 0 END), 0) as white_total,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'blue' THEN 1 ELSE 0 END), 0) as blue_total,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'red' THEN 1 ELSE 0 END), 0) as red_total,
    COALESCE(SUM(CASE WHEN LOWER(team_color) = 'green' THEN 1 ELSE 0 END), 0) as green_total
FROM public.match_teams;