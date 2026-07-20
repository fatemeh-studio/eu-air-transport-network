-- hub_ranking.sql
-- Which airports are the network's structural hubs, by persisted betweenness?
-- These are the nodes a betweenness-ordered targeted attack removes first. The
-- query reads the centralities NB02 wrote to network.db so NB04 can preview the
-- collapse order and confirm it against the attack's own ranking. NB02's
-- (directed-graph) betweenness and the undirected-giant betweenness NB04 attacks
-- with agree almost perfectly (Spearman rho ~ 0.99), so this list previews the hit order.
SELECT
    iata                     AS airport,
    city,
    country,
    in_degree + out_degree   AS total_links,
    ROUND(betweenness, 4)    AS betweenness
FROM nodes
WHERE betweenness IS NOT NULL
ORDER BY betweenness DESC
LIMIT 10;
