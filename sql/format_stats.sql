WITH match_counts AS (
    SELECT 
        COUNT(CASE WHEN pitch_aside = 9 THEN 1 END) as games_9,
        COUNT(CASE WHEN pitch_aside = 7 THEN 1 END) as games_7,
        COUNT(*) as games_overall
    FROM public.matches
),
stat_sums AS (
    SELECT 
        SUM(CASE WHEN m.pitch_aside = 9 THEN pms.goals ELSE 0 END) as goals_9,
        SUM(CASE WHEN m.pitch_aside = 7 THEN pms.goals ELSE 0 END) as goals_7,
        SUM(pms.goals) as goals_overall,
        
        SUM(CASE WHEN m.pitch_aside = 9 THEN pms.assists ELSE 0 END) as assists_9,
        SUM(CASE WHEN m.pitch_aside = 7 THEN pms.assists ELSE 0 END) as assists_7,
        SUM(pms.assists) as assists_overall,
        
        SUM(CASE WHEN m.pitch_aside = 9 THEN pms.own_goals ELSE 0 END) as og_9,
        SUM(CASE WHEN m.pitch_aside = 7 THEN pms.own_goals ELSE 0 END) as og_7,
        SUM(pms.own_goals) as og_overall,
        
        SUM(CASE WHEN m.pitch_aside = 9 AND pms.clean_sheet = TRUE THEN 1 ELSE 0 END) as cs_9,
        SUM(CASE WHEN m.pitch_aside = 7 AND pms.clean_sheet = TRUE THEN 1 ELSE 0 END) as cs_7,
        SUM(pms.clean_sheet = TRUE::integer) as cs_overall
    FROM public.player_match_stats pms
    JOIN public.matches m ON pms.match_id = m.id
)
SELECT * FROM match_counts, stat_sums;