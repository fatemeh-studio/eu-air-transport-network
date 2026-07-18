-- schema.sql
-- Persistent store for the European Air Transport Network (OpenFlights, June 2014).
--
--   nodes  — one row per airport that carries intra-European service (a graph
--            node, keyed by IATA). The centrality columns (in/out-degree,
--            betweenness, closeness, eigenvector, PageRank) and the Louvain
--            `community` column are declared NULLable here so notebooks 02 and
--            03 fill them with UPDATE statements, never ALTER TABLE.
--   edges  — one row per directed (source -> destination) operating route;
--            `weight` = number of distinct operating carriers on that pair.
--
-- Foreign keys are enforced by load_db.py, which sets `PRAGMA foreign_keys = ON`
-- on the connection before running this script. Tables are dropped in FK order
-- (edges before nodes) so re-running resets the database to the empty state.

DROP TABLE IF EXISTS edges;
DROP TABLE IF EXISTS nodes;

CREATE TABLE nodes (
    iata         TEXT    PRIMARY KEY,   -- 3-letter IATA code, e.g. 'VIE'
    name         TEXT,                  -- airport name
    city         TEXT,
    country      TEXT,
    lat          REAL,
    lon          REAL,
    -- Filled by 02_centrality_stats.ipynb (NULL until then):
    in_degree    INTEGER,
    out_degree   INTEGER,
    betweenness  REAL,
    closeness    REAL,
    eigenvector  REAL,
    pagerank     REAL,
    -- Filled by 03_community_detection.ipynb (NULL until then):
    community    INTEGER
);

CREATE TABLE edges (
    source       TEXT    NOT NULL,
    destination  TEXT    NOT NULL,
    weight       INTEGER NOT NULL CHECK (weight > 0),  -- distinct operating carriers
    PRIMARY KEY (source, destination),
    FOREIGN KEY (source)      REFERENCES nodes(iata),
    FOREIGN KEY (destination) REFERENCES nodes(iata)
);

-- The composite PK indexes (source, destination) left-to-right: it serves
-- out-edge lookups (WHERE source = ?) but NOT destination-only lookups. Add the
-- reverse index so "who flies INTO this airport" queries stay indexed as well.
CREATE INDEX idx_edges_destination ON edges (destination);