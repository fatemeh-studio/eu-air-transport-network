# PROGRESS — European Air Transport Network

**Last updated:** 2026-07-19
**Current status:** **NB02 complete.** `02_centrality_stats.ipynb` runs clean top-to-bottom
in a single file (centralities → RQ1 → degree distribution → small-world), writing all six
centrality columns for 559 nodes into `network.db` and saving
`sql/queries/top_airports_by_betweenness.sql`. Research Question 1 is answered — and the
"Vienna as East–West bridge" hypothesis is **rejected** by the 2014 operating-carrier data
(VIE is a mid-tier hub: betweenness rank 42 / 42 / 45 on the global / all-East / CEE tests).
The degree distribution is broad-scale / truncated (NOT scale-free); the network is strongly
small-world (σ ≈ 11). Next: **NB03** — Louvain community detection, delivered as one
complete notebook.

> **House voice:** the format of *this file* is the project's prose style — match its
> density, its `decision → reason` arrows, its **bold** concept lead-ins, and its dating
> of every claim when writing notebook markdown, README text, or new entries here.
> Do not reinvent the format.

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
- [x] `sql/queries/top_airports_by_betweenness.sql`  *(NB02)*
- [ ] `sql/queries/community_country_distribution.sql`  *(NB03)*

### Notebooks
- [x] `01_graph_construction.ipynb`
- [x] `02_centrality_stats.ipynb`
- [ ] `03_community_detection.ipynb`
- [ ] `04_resilience_analysis.ipynb`

### Other
- [ ] `requirements.txt`  *(remember to add `python-kaleido` AND `powerlaw` — see watch-outs)*
- [ ] `README.md` (final)
- [x] `figures/` (populated — `route_map.png`, `degree_distribution.png`)
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

- **Eigenvector centrality computed on the undirected giant component**, not the DiGraph → 
  eigenvector_centrality_numpy raises AmbiguousSolution on graphs that aren't connected + strongly connected (ours is neither). Off-giant nodes = 0.0. PageRank is the directed-influence measure. Betweenness/closeness are unweighted (weight = carrier-count service proxy, not a distance).

- **Notebooks are delivered as single, complete files — no part 1 / part 2 split** → NB02
  (centralities + RQ1 + degree distribution + small-world) ran clean top-to-bottom in one
  file; the planned two-chat split proved an unnecessary hedge. NB03 and NB04 follow the same
  rule: one scoped notebook, built and delivered complete in a single chat.

- **RQ1 tested three ways with subset betweenness, and the hypothesis was rejected** →
  global betweenness rewards **intermediaries, not endpoints** (a super-hub is an endpoint;
  a tree-like periphery's gateway is the bottleneck), so `betweenness_centrality_subset`
  over East↔West and CEE↔rest paths is the honest test of "Vienna as bridge". Vienna lands
  at rank 42 / 42 / 45. Reported as-is: VIE is a mid-tier hub, not the East–West bridge —
  the LCCs had already rewired CEE to point-to-point by 2014 (top CEE gateways are STN, BGY,
  LTN, DUB), and the codeshare filter hides Austrian's Star Alliance feed. *Structural
  centrality ≠ commercial importance* — the same lesson NB01's degree ranking flagged.

- **Power-law fit via the `powerlaw` package (Clauset–Shalizi–Newman), not OLS on log-log**
  → OLS on a binned CCDF is a biased estimator; CSN uses MLE for α with a KS-chosen k_min
  plus a likelihood-ratio test against alternatives. Result: the pure power law is decisively
  beaten by both log-normal (R = −5.69) and truncated power law (R = −6.99), p < 0.001 →
  broad-scale / truncated, NOT clean scale-free (the finite-capacity ceiling of physical
  airport infrastructure). New pip dependency: `powerlaw`, imported inside the fit cell only.

- **Small-world σ against a seeded ER ensemble (20 realisations)** → σ = (C/C_rand)/(L/L_rand)
  on the undirected giant component. σ ≈ 11 (C = 0.42 vs 0.035 random; L = 2.71 vs 2.46).
  Strongly small-world — the structural precondition for NB04's targeted-attack collapse.

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

Centrality columns now populated (NB02): all six non-NULL for 559 / 559 nodes. `community`
still NULL, awaiting NB03.

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

**NB02 — Centrality & structure:**
- all six centralities written to `network.db`: 559 / 559 nodes
- top betweenness (global): IST 0.0905, ARN 0.0797, OSL 0.0751, ATH 0.0638, STN 0.0546
- **Vienna betweenness: rank 40 / 479** (>5-airport countries), rank 42 / 559 global, β = 0.0106
- legacy hubs — high degree, mid betweenness (endpoint-not-intermediary): AMS deg#4 / btw#16,
  CDG #7 / #17, FRA #8 / #26, MUC #10 / #24, LHR #27 / #49 (LHR low degree = slot-constrained + codeshare-filtered)
- East–West subset betweenness: **VIE rank 42** (all-East), **rank 45** (CEE-only) — NOT a
  standout bridge; top CEE gateways are LCC bases STN, BGY, LTN, DUB + aggregator OTP
- degree distribution: MLE α = 1.59 (k_min 3); **power law decisively beaten** by log-normal
  (R = −5.69, p ≈ 0) and truncated power law (R = −6.99, p ≈ 0) → broad-scale / truncated,
  NOT clean scale-free
- small-world: C = 0.421 vs C_rand 0.035, L = 2.71 vs L_rand 2.46, **σ = 10.9** (≫ 1)
- **RQ1 answer: Vienna is a mid-tier hub, not the East–West bridge (2014).** Honest finding;
  structural centrality ≠ commercial importance.

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
  Ukrainian and Russian airspace closed to EU carriers in 2022. The 2014 finding is that VIE
  is a mid-tier hub, **not** the East–West bridge — report it dated, and note that the
  present-day picture differs. This is the one place where staleness touches the narrative.

- **RQ1: "scale-free" and "Vienna is the bridge" are BOTH off-limits as claims.** The CSN
  likelihood-ratio test (NB02) decisively favours log-normal / truncated power law over a
  pure power law (R = −5.7 / −7.0, p < 0.001) → README wording is "heavy-tailed / broad-scale
  (truncated power law)", never "scale-free with α = …" (the MLE α = 1.59 is a tail-slope
  descriptor, not evidence of scale-freeness). And the Vienna betweenness ranks (42/42/45)
  say VIE is a mid-tier hub, not the East–West bridge — the honest, defensible headline.

- **New dependency: `powerlaw`** (NB02 degree fit). Install with
  `pip install powerlaw --break-system-packages` inside the conda env; add `powerlaw>=1.5`
  to `requirements.txt`. Imported inside NB02's fit cell (not at the top), so the rest of the
  notebook runs even if it is absent.

- **East/West partition is a modelling choice (NB02).** The all-East set includes Russia/CIS,
  whose Moscow-centred flows dominate the East–West ranking; the CEE-only set excludes them.
  Both are stated in-notebook and adjustable — neither changes the Vienna conclusion.

- **Codeshare filter understates alliance hubs (surfaced in NB02).** Dropping codeshares
  removes Austrian/Star Alliance CEE feed (VIE's marketed gateway role) and slot-constrained
  alliance traffic (LHR's degree is only #27). A real, defensible limitation — name it in the
  README beside the Vienna finding.

- **Berlin artifact:** TXL and SXF appear as separate airports; BER does not exist in the
  data (opened Oct 2020). Do not "fix" this — it is correct for 2014. (Verified in NB01.)

- **Coverage mismatch between the two files — RESOLVED (NB01):** airports.dat holds
  ~7 700 airports globally, routes.dat touches only 3 321. The bounding box catches
  1,029 EU airports, but the graph is induced from route endpoints, so only the 559 with
  real service become nodes — isolated airfields never enter the graph. No isolated-node
  pruning step needed.

- **schema.sql pre-declares the columns NB02/NB03 will fill — DONE.** Implemented in
  `sql/schema.sql`. NB02 `UPDATE`s betweenness, closeness, eigenvector, pagerank,
  in_degree, out_degree (done); NB03 will `UPDATE` community. All declared NULLable, so later
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

**Task:** NB03 (complete, one notebook) — Louvain community detection answering Research
Question 2 (do aviation communities follow country borders?). On the undirected giant
component with `python-louvain`: run resolution 0.5 / 1.0 / 1.5 and report modularity Q for
each, pick a working resolution, assign community labels back to nodes and `UPDATE` the
`community` column in `network.db`, and write `sql/queries/community_country_distribution.sql`
(dominant country per community). Both visualisations go in the same notebook — a geographic
Plotly map coloured by community, and a PyVis force-directed graph (colour = community,
size = degree) saved to `network_viz/community_network.html`. Analyse whether communities
align with geography, country, or airline alliances. Deliver as a single complete
`03_community_detection.ipynb` — **not** split into parts.
**Start message:** "Current state: see PROGRESS.md. Today's task: NB03 (complete, one notebook) — Louvain community detection: resolution sweep 0.5/1.0/1.5 + modularity Q, UPDATE the community column, community_country_distribution.sql, geographic Plotly community map + PyVis html."
**Relevant uploaded files Claude should read:** PROGRESS.md, src/build_graph.py, src/utils.py, src/load_db.py
