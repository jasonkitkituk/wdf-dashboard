-- sql/rank_clean_sheet.sql
WITH player_cs_stats AS (
    SELECT 
        pl.id AS player_id,
        pl.name AS player_name,
        COUNT(CASE WHEN pms.clean_sheet = true THEN 1 END) AS clean_sheets,
        COUNT(pms.match_id) AS appearances
    FROM player_match_stats pms
    JOIN players pl ON pms.player_id = pl.id
    JOIN matches m ON pms.match_id = m.id
    WHERE pl.is_active = true
      AND (%s::integer IS NULL OR m.pitch_aside = %s::integer)
    GROUP BY pl.id, pl.name
    HAVING COUNT(CASE WHEN pms.clean_sheet = true THEN 1 END) > 0  -- 只列出至少 1 次零封的球員
)
SELECT 
    ROW_NUMBER() OVER (
        ORDER BY p.clean_sheets DESC, 
                 p.appearances ASC, 
                 p.player_name ASC
    ) AS rank,
    p.player_name,
    p.clean_sheets,
    p.appearances
FROM player_cs_stats p
ORDER BY clean_sheets DESC, appearances ASC, p.player_name ASC
LIMIT 10;