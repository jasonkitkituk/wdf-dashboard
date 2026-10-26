SELECT 
    SUM(CASE WHEN team_color = 'Black' AND result = 'Win' THEN 1 ELSE 0 END) as black_win,
    SUM(CASE WHEN team_color = 'White' AND result = 'Win' THEN 1 ELSE 0 END) as white_win,
    SUM(CASE WHEN team_color = 'Blue' AND result = 'Win' THEN 1 ELSE 0 END) as blue_win,
    SUM(CASE WHEN team_color = 'Red' AND result = 'Win' THEN 1 ELSE 0 END) as red_win,
    SUM(CASE WHEN team_color = 'Green' AND result = 'Win' THEN 1 ELSE 0 END) as green_win,

    SUM(CASE WHEN team_color = 'Black' AND result = 'Draw' THEN 1 ELSE 0 END) as black_draw,
    SUM(CASE WHEN team_color = 'White' AND result = 'Draw' THEN 1 ELSE 0 END) as white_draw,
    SUM(CASE WHEN team_color = 'Blue' AND result = 'Draw' THEN 1 ELSE 0 END) as blue_draw,
    SUM(CASE WHEN team_color = 'Red' AND result = 'Draw' THEN 1 ELSE 0 END) as red_draw,
    SUM(CASE WHEN team_color = 'Green' AND result = 'Draw' THEN 1 ELSE 0 END) as green_draw,

    SUM(CASE WHEN team_color = 'Black' AND result = 'Lose' THEN 1 ELSE 0 END) as black_lose,
    SUM(CASE WHEN team_color = 'White' AND result = 'Lose' THEN 1 ELSE 0 END) as white_lose,
    SUM(CASE WHEN team_color = 'Blue' AND result = 'Lose' THEN 1 ELSE 0 END) as blue_lose,
    SUM(CASE WHEN team_color = 'Red' AND result = 'Lose' THEN 1 ELSE 0 END) as red_lose,
    SUM(CASE WHEN team_color = 'Green' AND result = 'Lose' THEN 1 ELSE 0 END) as green_lose,

    SUM(CASE WHEN team_color = 'Black' THEN 1 ELSE 0 END) as black_total,
    SUM(CASE WHEN team_color = 'White' THEN 1 ELSE 0 END) as white_total,
    SUM(CASE WHEN team_color = 'Blue' THEN 1 ELSE 0 END) as blue_total,
    SUM(CASE WHEN team_color = 'Red' THEN 1 ELSE 0 END) as red_total,
    SUM(CASE WHEN team_color = 'Green' THEN 1 ELSE 0 END) as green_total
FROM public.match_teams;