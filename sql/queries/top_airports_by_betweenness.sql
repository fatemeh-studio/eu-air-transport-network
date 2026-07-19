-- top_airports_by_betweenness.sql
-- Research Question 1: which airports are the structural bridges of the 2014
-- European air network, and where does Vienna (VIE) rank among them?
--
-- Ranks airports by betweenness centrality, restricted to countries that field
-- more than five airports in the graph -- so the ranking reflects well-sampled
-- national systems rather than single-airport countries. The is_vienna flag
-- marks VIE so its position is visible directly in the result set.
--
-- Rank is computed WITHIN the qualifying pool. For a global rank across every
-- airport, remove the JOIN to qualifying_countries.
-- Requires SQLite >= 3.25 (RANK() window function). Data vintage: OpenFlights June 2014.

WITH qualifying_countries AS (
    -- Countries represented by more than five airports in the node set.
    SELECT country
      FROM nodes
     WHERE country IS NOT NULL
     GROUP BY country
    HAVING COUNT(*) > 5
)
SELECT
    RANK() OVER (ORDER BY n.betweenness DESC)   AS betweenness_rank,
    n.iata                                      AS airport_code,
    n.name                                      AS airport_name,
    n.city                                      AS city,
    n.country                                   AS country,
    ROUND(n.betweenness, 6)                     AS betweenness,
    CASE WHEN n.iata = 'VIE' THEN 1 ELSE 0 END  AS is_vienna
  FROM nodes AS n
  JOIN qualifying_countries AS q
    ON n.country = q.country
 WHERE n.betweenness IS NOT NULL
 ORDER BY betweenness_rank, airport_code;
 