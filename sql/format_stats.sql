WITH match_counts AS (
    SELECT 
        COUNT(CASE WHEN pitch_aside = 9 THEN 1 END) as games_9,
        COUNT(CASE WHEN pitch_aside = 7 THEN 1 END) as games_7,
        COUNT(*) as games_overall
    FROM public.matches
),
stat_sums AS (
    SELECT 
        COALESCE(SUM(CASE WHEN m.pitch_aside = 9 THEN pms.goals ELSE 0 END), 0) as goals_9,
        COALESCE(SUM(CASE WHEN m.pitch_aside = 7 THEN pms.goals ELSE 0 END), 0) as goals_7,
        COALESCE(SUM(pms.goals), 0) as goals_overall,
        
        COALESCE(SUM(CASE WHEN m.pitch_aside = 9 THEN pms.assists ELSE 0 END), 0) as assists_9,
        COALESCE(SUM(CASE WHEN m.pitch_aside = 7 THEN pms.assists ELSE 0 END), 0) as assists_7,
        COALESCE(SUM(pms.assists), 0) as assists_overall,
        
        COALESCE(SUM(CASE WHEN m.pitch_aside = 9 THEN pms.own_goals ELSE 0 END), 0) as og_9,
        COALESCE(SUM(CASE WHEN m.pitch_aside = 7 THEN pms.own_goals ELSE 0 END), 0) as og_7,
        COALESCE(SUM(pms.own_goals), 0) as og_overall,
        
        COALESCE(SUM(CASE WHEN m.pitch_aside = 9 AND pms.clean_sheet = TRUE THEN 1 ELSE 0 END), 0) as cs_9,
        COALESCE(SUM(CASE WHEN m.pitch_aside = 7 AND pms.clean_sheet = TRUE THEN 1 ELSE 0 END), 0) as cs_7,
        COALESCE(SUM(CASE WHEN pms.clean_sheet = TRUE THEN 1 ELSE 0 END), 0) as cs_overall
    FROM public.player_match_stats pms
    JOIN public.matches m ON pms.match_id = m.id
)
SELECT * FROM match_counts, stat_sums; 