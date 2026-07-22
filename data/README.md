# Data — OpenFlights airport & route tables

Two static, comma-separated files from [OpenFlights](https://openflights.org/data.html),
tracked directly in git (≈12 MB total — small enough to commit, so the analysis needs
no download script, no API key and no quota).

- `airports.dat` — ~7,700 airports worldwide
- `routes.dat` — 67,663 routes / 3,321 airports / 548 airlines worldwide

**License:** OpenFlights [Open Database License](https://openflights.org/data.html). Credit OpenFlights when reusing.

---

## ⚠️ Data vintage — June 2014

`routes.dat` is a **frozen June 2014 snapshot**. OpenFlights' route provider ceased
updates that month, and OpenFlights labels the route data *"of historical value only."*
This is accepted deliberately, not by oversight:

- The three research questions are **topological** — degree distribution (broad-scale /
  truncated), community structure, percolation threshold. These are structural invariants
  that do not flip year to year. Snapshot analysis is standard in the network-science
  literature (Guimerà & Amaral, *PNAS* 2005; Barrat et al., *PNAS* 2004).
- **Reproducibility outweighs freshness**: a committed 12 MB file regenerates the whole 
  pipeline offline, forever.

Every figure, table and claim in this project is therefore a **June 2014** statement and
is dated as such. Two artifacts of the vintage worth knowing: **Berlin Brandenburg (BER)
does not exist** in the data (it opened October 2020 — Berlin appears as TXL + SXF), and
**Vienna's position understates its post-2018 growth** (Wizz Air / Ryanair / Lauda bases).

---

## Loading notes

- **No header row.** Column names must be supplied manually (see schemas below; they live
  in code as `AIRPORT_COLS` / `ROUTE_COLS` in `src/build_graph.py`).
- **NULL sentinel is `\N`**, not an empty string — load with `na_values=[r"\N"]`
  (note the raw string; a bare `"\N"` literal is a `SyntaxError` in Python).

---

## `airports.dat` — 14 columns

| # | Column | Notes |
|---|---|---|
| 1 | Airport ID | OpenFlights internal ID |
| 2 | Name | Airport name |
| 3 | City | Served city |
| 4 | Country | Country name |
| 5 | IATA | 3-letter code (e.g. `VIE`) — the graph's node key |
| 6 | ICAO | 4-letter code |
| 7 | Latitude | decimal degrees |
| 8 | Longitude | decimal degrees |
| 9 | Altitude | feet |
| 10 | Timezone | hours offset from UTC |
| 11 | DST | daylight-savings code |
| 12 | Tz | Olson tz database name |
| 13 | Type | e.g. `airport` |
| 14 | Source | data provenance |

## `routes.dat` — 9 columns

| # | Column | Notes |
|---|---|---|
| 1 | Airline | 2-letter airline code |
| 2 | Airline ID | OpenFlights airline ID |
| 3 | Source airport | IATA of origin |
| 4 | Source airport ID | OpenFlights airport ID |
| 5 | Destination airport | IATA of destination |
| 6 | Destination airport ID | OpenFlights airport ID |
| 7 | Codeshare | `Y` if a codeshare (sold by one carrier, operated by another) |
| 8 | Stops | number of stops (0 = direct) |
| 9 | Equipment | aircraft type codes |

---

## How this becomes the graph

Airports are filtered to a **European bounding box** (lat 34–72°N, lon −25–45°E — continental
Europe + UK + Cyprus, excluding Russia east of the Urals), then **nodes are induced from
route endpoints** rather than from the airport table. So the 1,029 airports inside the box
collapse to the **559 that actually carry intra-European service** — isolated airfields
never enter the graph, and no post-hoc pruning is needed.

Edges are built from operating routes only. The filtering trail:

| Step | Rows |
|---|---:|
| Raw EU–EU route rows | 16,780 |
| − codeshares (`Codeshare == 'Y'`) | −2,762 |
| − multi-leg services (`Stops > 0`) | −1 |
| Operating legs | 14,017 |
| **Distinct directed edges** (`weight` = distinct operating carriers per pair) | **10,287** |

**Edge weight is a service-level proxy**, not traffic — `routes.dat` has no frequency or
capacity data, so it counts *how many operating carriers* fly a pair, not how many seats or
flights. The codeshare filter is deliberate (an unfiltered Lufthansa flight would be counted
up to 5× across Star Alliance partners) but has a known side effect: it **understates
alliance hubs** by removing marketed feed (e.g. Heathrow's slot-constrained, codeshare-heavy
traffic, and Austrian's Star Alliance gateway role at Vienna).

Source: [OpenFlights data](https://openflights.org/data.html).
