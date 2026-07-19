-- community_country_distribution.sql
-- RQ2 — do aviation communities follow national borders? For each Louvain
-- community this ranks its member countries and returns the dominant one plus
-- its share of the community. A high share means the community is essentially a
-- single country's domestic network; a low share means Louvain has fused several
-- countries into a super-regional bloc that crosses borders.
WITH community_country AS (
    SELECT community,
           country,
           COUNT(*) AS airports_in_country
    FROM   nodes
    WHERE  community IS NOT NULL          -- off-giant nodes carry no community label
    GROUP  BY community, country
),
ranked AS (
    SELECT community,
           country,
           airports_in_country,
           SUM(airports_in_country)  OVER (PARTITION BY community) AS community_size,
           COUNT(*)                  OVER (PARTITION BY community) AS countries_in_community,
           ROW_NUMBER()              OVER (PARTITION BY community
                                           ORDER BY airports_in_country DESC,
                                                    country ASC)     AS country_rank
    FROM   community_country
)
SELECT community              AS community_id,
       community_size         AS airports_in_community,
       countries_in_community AS distinct_countries,
       country                AS dominant_country,
       airports_in_country    AS dominant_country_airports,
       ROUND(100.0 * airports_in_country / community_size, 1)
                              AS dominant_country_pct
FROM   ranked
WHERE  country_rank = 1
ORDER  BY airports_in_community DESC;
