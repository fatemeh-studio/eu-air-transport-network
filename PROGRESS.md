# PROGRESS — European Air Transport Network

**Last updated:** 2026-07-18
**Current status:** SQLite persistence layer complete. `sql/schema.sql` +
`src/load_db.py` built, tested, and committed; `src/utils.py` gained SQL path constants
(`SQL_DIR`, `SCHEMA_PATH`, `SQL_QUERIES_DIR`). Running `python src/load_db.py` loads
559 nodes + 10,287 directed edges into `network.db` and passes the `pd.read_sql`
round-trip — node/edge counts match the graph, and all seven centrality/community
columns are present but NULL, awaiting NB02/NB03. Next: **NB02** — centrality analysis
(starting with the six centralities + SQLite write-back + the Vienna betweenness query).

---

## Completed files

### Data
- [x] `data/airports.dat` — downloaded from OpenFlights
- [x] `data/routes.dat` — downloaded from OpenFlights
- [ ] `data/README.md`

### Source modules
- [x] `src/utils.py` — added SQL path constants
- [x] `src/build_graph.py`
- [x] `src/load_db.py`

### SQL
- [x] `sql/schema.sql`
- [ ] `sql/queries/top_airports_by_betweenness.sql`  *(NB02 part 1)*
- [ ] `sql/queries/community_country_distribution.sql`  *(NB03)*

### Notebooks
- [x] `01_graph_construction.ipynb`
- [ ] `02_centrality_stats.ipynb`
- [ ] `03_community_detection.ipynb`
- [ ] `04_resilience_analysis.ipynb`

### Other
- [ ] `requirements.txt`  *(remember to add `python-kaleido` — see watch-outs)*
- [ ] `README.md` (final)
- [x] `figures/` (populated — `route_map.png`)
- [x] `.gitattributes` (nbstripout filter)
- [x] `.nojekyll` (Pages serves reports/ as-is)

## Reports (Quarto)
- [x] nbstripout installed (`nbstripout --status` → OK)
- [x] Quarto installed in the conda env (`quarto check` → OK)
- [ ] GitHub Pages enabled (Settings → Pages → Deploy from a branch → main / docs)

---

## Key decisions made

*Add entries here as the project evolves. Format: decision → reason*

- **Europe bounding box:** lat 34–72°N, lon –25–45°E
  → Covers continental Europe + UK + Cyprus; excludes Russia east of Urals

- **Graph type:** `nx.DiGraph` for directed analysis (centrality, PageRank);
  `nx.Graph` undirected projection for community detection and small-world test
  → Two separate graph objects, both built in `src/build_graph.py`

- **Data vintage:** `routes.dat` is a frozen June 2014 snapshot — OpenFlights' route
  provider ceased updates then, and OpenFlights labels the data "of historical value
  only" (67 663 routes / 3 321 airports / 548 airlines globally)
  → Accepted deliberately, not by oversight. The three research questions are
  topological (scale-free structure, community structure, percolation threshold) —
  structural invariants that do not flip year to year. Snapshot analysis is standard
  in the literature (Guimerà & Amaral, PNAS 2005; Barrat et al., PNAS 2004).
  Reproducibility (12 MB tracked in git, no API key, no quota) outweighs freshness for
  a portfolio repo. MUST be stated explicitly in the README.

- **Codeshare filtering:** drop all rows where the codeshare column == 'Y'; keep only
  operating carriers
  → A codeshare row is a flight sold by one carrier but operated by another.
  Unfiltered, a single physical Lufthansa flight is counted up to 5× via Star Alliance
  partners, and the weight would measure "how many partners sell this route" rather
  than "how much service exists on it".

- **Edge weight:** weight = number of distinct *operating* carriers per
  (source, destination) pair
  → Service-level proxy. NOT traffic, frequency, or capacity — routes.dat has no
  frequency data, so Barrat-style seat-weighted analysis is not possible. State this
  limitation explicitly in NB01 and the README.

- **Stops filter:** keep only rows where Stops == 0
  → Rows with stops > 0 are multi-leg services; treating them as direct edges creates
  phantom links that do not exist in the physical network.

- **build_graph.py interface:** loading/filtering separated from graph construction.
  Graph functions accept a tidy (source, destination, weight) DataFrame and return the
  graph objects.
  → Keeps a second data source addable later as a config change rather than a rewrite.
  Separation of concerns, not speculative abstraction.

- **Node identifier = 3-letter IATA code** (NB01), and nodes are *induced from route
  endpoints* rather than from the airport table
  → Readable codes (VIE, FRA, LHR); airports lacking a valid IATA are excluded.
  Because nodes come from edges, the bounding box's 1,029 airports collapse to the 559
  that actually carry intra-European service — the coverage-mismatch / isolated-node
  question is resolved by construction, no post-hoc pruning. `filter_europe` also
  drops duplicate IATA codes (keep first).

- **Undirected-projection edge weight = sum of the two directional weights** (w_AB + w_BA)
  (NB01)
  → A symmetric "total operating-carrier service" on the link. Reciprocal edges are
  collapsed explicitly in `build_undirected()`; NetworkX's `to_undirected()` would
  silently keep only one direction's weight, so the projection is built by hand.

- **Second data source deferred:** Eurostat `avia_par_<cc>` (real passenger and flight
  counts per airport pair, current through 2024, free API, no key) is a candidate for a
  possible NB05 "2014 vs 2024" extension.
  → Do NOT start until NB04 is committed. Four notebooks first.

- **nbstripout as a git clean filter** (`--install --attributes .gitattributes`)
  → Outputs never enter git history: readable diffs, small repo, no figure blobs.
    Working copies keep their outputs; only the committed blob is stripped.

- **Quarto from conda-forge into `eu-air-network`, not the system .deb**
  → No sudo, version travels with the env, consistent with the conda-only rule.

- **Site rendered as a Quarto website** (_quarto.yml, type: website, output-dir: docs)
  → One linked site with a shared docs/site_libs/, not N standalone HTMLs. docs/ IS
    committed — the documented exception to the no-build-artifacts rule. Still --execute
    (stripped notebooks carry no stored outputs).

- **Pages source = main / docs**, .nojekyll at repo root (Quarto also writes docs/.nojekyll)
  → Website output lives in docs/. The reports/ folder is no longer used.

- **Nodes table sourced from the graph, not airports_eu** → the airport table has ~1,029
  bounding-box rows but only 559 are graph nodes; sourcing from digraph.nodes() guarantees
  the nodes table == the graph, no orphan rows for NB02's UPDATEs to strand.

- **load_db writes structure only; all 7 centrality/community columns stay NULL** → filled
  by NB02/NB03 via UPDATE. Re-running load_db.py drops + recreates both tables and wipes
  those results — intentional "reset to structural state", not a bug.

- **Edges stored directed (10,287)** with composite PK (source, destination) + FK to nodes
  + reverse index on destination; undirected projection is rebuilt from build_graph in
  NB03/NB04.

---

## Current SQLite schema

Two tables. Centrality + community columns are pre-declared NULLable so NB02/NB03 run
`UPDATE`, never `ALTER TABLE`. FK is enforced by `load_db.py` (`PRAGMA foreign_keys = ON`
on the connection). `network.db` is gitignored — regenerated by `python src/load_db.py`.

```sql
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
```

---

## Graph statistics (NB01)

| Metric | DiGraph | Undirected |
|---|---|---|
| Total EU airports (nodes) | 559 | 559 |
| Total routes (edges) | 10,287 | 5,206 |
| Largest connected component | 544 (97.3%) | 544 (97.3%) |
| Number of components | 5 | 5 |
| Network density | 0.033 | 0.033 |

*(Filtering trail: 16,780 raw EU–EU route rows → −2,762 codeshares → −1 multi-stop
→ 14,017 operating legs → 10,287 distinct directed edges.)*

---

## Key results so far

*Add findings here as each notebook is completed.*

**NB01 — Graph construction:**
- 559 nodes
- 10,287 directed edges
- giant component 97.3% (5 components)
- degree≠traffic — Stansted tops degree, VIE degree-rank 29 (betweenness is the real VIE story, deferred to NB02).

**Data layer (schema + load_db):**
- `network.db` round-trip verified: 559 nodes / 10,287 edges, 0 nodes scored (all
  centrality/community columns NULL until NB02/NB03).

**NB02 — Centrality:**
- Vienna (VIE) betweenness rank: —
- Power law exponent: —
- Small-world σ coefficient: —

**NB03 — Community detection:**
- Number of communities (Louvain, resolution=1.0): —
- Modularity Q: —
- Do communities follow country borders? —

**NB04 — Resilience:**
- Critical threshold f_c (targeted attack): —
- Critical threshold f_c (random failure): —

---

## Known issues / watch out for

*Add as discovered during development.*

- **Never call this network "current".** It is the June 2014 route topology. Date every
  claim in notebooks, README, and figure titles.

- **Vienna narrative is a 2014 statement.** VIE's 2014 degree/betweenness understates its
  position today: Wizz Air / Ryanair / Lauda built VIE bases from 2018 onward, and
  Ukrainian and Russian airspace closed to EU carriers in 2022. "VIE as East–West bridge"
  is still a real finding — but it describes 2014 and must be dated as such. This is the
  one place where staleness touches the project narrative directly.

- **Berlin artifact:** TXL and SXF appear as separate airports; BER does not exist in the
  data (opened Oct 2020). Do not "fix" this — it is correct for 2014. (Verified in NB01.)

- **Coverage mismatch between the two files — RESOLVED (NB01):** airports.dat holds
  ~7 700 airports globally, routes.dat touches only 3 321. The bounding box catches
  1,029 EU airports, but the graph is induced from route endpoints, so only the 559 with
  real service become nodes — isolated airfields never enter the graph. No isolated-node
  pruning step needed.

- **schema.sql pre-declares the columns NB02/NB03 will fill — DONE.** Implemented in
  `sql/schema.sql`. NB02 will `UPDATE` betweenness, closeness, eigenvector, pagerank,
  in_degree, out_degree; NB03 will `UPDATE` community. All declared NULLable, so later
  notebooks run `UPDATE`, not `ALTER TABLE`. Final shape:
  `nodes(iata PK, name, city, country, lat, lon, in_degree, out_degree, betweenness,
  closeness, eigenvector, pagerank, community)`,
  `edges(source, destination, weight, PK(source,destination), FK->nodes, idx on destination)`.

- **Re-running `load_db.py` WIPES NB02/NB03 results.** `schema.sql` drops + recreates both
  tables, so any centrality/community values written by later notebooks are lost. Run
  `load_db.py` once up front; re-run only to reset from scratch, then re-run NB02/NB03.

- **FK enforcement is connection-level, not baked into the .sql file.** `load_db.py` sets
  `PRAGMA foreign_keys = ON` before writing, so orphan edges are rejected. Running
  `schema.sql` directly via the `sqlite3` CLI won't enforce FK (pragma off by default),
  but the DROP/CREATE order is CLI-safe either way. `write_tables()` also guards with an
  explicit orphan check that raises a readable `ValueError` before any insert.

- **New dependency: `kaleido`** (Plotly static PNG export, used by NB01's banner cell).
  Install with `conda install -c conda-forge python-kaleido` (self-contained, no separate
  Chrome install needed). Add `python-kaleido` to `requirements.txt` / the env block.
  NB01's export cell is wrapped in try/except, so restart-and-run-all stays clean even if
  it's absent — but the banner PNG won't regenerate without it.

- **`\N` is the NULL sentinel** in OpenFlights .dat files, not an empty string. Pass
  `na_values=[r"\N"]` on load. Note the raw string: a plain `"\N"` literal is a
  SyntaxError in Python.

- **Neither file has a header row.** Column names must be supplied manually — both schemas
  are in GITHUB_SETUP.md Step 4 (and now in `AIRPORT_COLS` / `ROUTE_COLS` in build_graph.py).

- `nbstripout --install` writes to `.git/config`, which is not committed. Re-run it after
  any fresh clone, BEFORE the first `git add` of a notebook.

- `quarto render <nb>.ipynb` does not execute cells by default — always pass `--execute`.

- Website mode: do NOT use --embed-resources. Assets live in docs/site_libs/ and MUST be
  committed with docs/, or the published site loses its CSS/JS.

- plotly.min.js sits once in docs/site_libs/ (~3.5 MB). Check `du -sh docs` — still under
  the per-file 5 MB rule because it's shared, not embedded four times.

- A website needs index.qmd at the root; the explicit render: list stops Quarto pulling
  README.md and data/README.md in as stray pages.

- Cursor's Quarto extension can't see a conda-installed Quarto unless Cursor is launched
  from an activated env (`conda activate eu-air-network && cursor .`). Irrelevant while
  rendering from the CLI, which is the plan.

---

## Next chat

**Task:** NB02 part 1 — compute the six centralities on the DiGraph (in-degree,
out-degree, betweenness, closeness, eigenvector, PageRank), `UPDATE` them into the `nodes`
table, and write `sql/queries/top_airports_by_betweenness.sql` (rank airports by
betweenness for countries with >5 airports in the dataset, showing VIE's rank explicitly).
This answers Research Question 1 (Vienna as an East–West bridge, 2014) and populates the
DB for the rest of NB02.
*(Degree distribution / power-law fit / small-world σ → NB02 part 2, a separate chat —
NB02 is too large for one chat.)*
**Start message:** "Current state: see PROGRESS.md. Today's task: NB02 part 1 — six centralities + UPDATE into nodes + top_airports_by_betweenness.sql"
**Relevant uploaded files Claude should read:** PROGRESS.md, src/build_graph.py, src/utils.py, src/load_db.py