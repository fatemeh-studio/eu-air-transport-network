"""Construct the European Air Transport Network from OpenFlights .dat files.

Pipeline (loading/filtering is kept separate from graph construction so a second
data source can be dropped in as a config change, not a rewrite):

    load_airports  ->  filter_europe        (bounding box + valid IATA)
    load_routes    ->  filter_routes        (stops == 0, drop codeshares,
                                             both endpoints inside Europe)
                   ->  build_edge_list       (tidy source/destination/weight)
                   ->  build_digraph         (directed, weighted nx.DiGraph)
                   ->  build_undirected      (undirected projection)

Key modelling decisions (see PROGRESS.md for the reasoning):
  * Nodes are keyed by 3-letter IATA code and induced from route endpoints, so
    airports with zero intra-European routes never enter the graph — the
    isolated-node question is resolved by construction.
  * ``weight`` = number of distinct *operating* carriers on a directed
    (source, destination) pair. A service-level proxy, NOT traffic/frequency/
    capacity — routes.dat carries no frequency data.
  * Undirected weight = sum of the two directional weights (total operating-
    carrier service on the link).

Data vintage: OpenFlights **June 2014** snapshot. This is not the current
network; every downstream figure is dated accordingly.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd

from utils import AIRPORTS_DAT, ROUTES_DAT

# --------------------------------------------------------------------------- #
# Constants (no magic numbers scattered through the code)
# --------------------------------------------------------------------------- #
# Europe bounding box: continental Europe + UK + Cyprus, excludes Russia east
# of the Urals. (min, max) in degrees.
EUROPE_LAT: tuple[float, float] = (34.0, 72.0)
EUROPE_LON: tuple[float, float] = (-25.0, 45.0)

# OpenFlights NULL sentinel. Raw string on purpose: a plain "\N" is a Python
# SyntaxError, and the file uses a literal backslash-N, not an empty field.
NA_SENTINEL: str = r"\N"

IATA_CODE_LEN: int = 3          # valid IATA codes are exactly 3 letters
CODESHARE_FLAG: str = "Y"       # routes.dat marks a codeshare row with "Y"
DIRECT_FLIGHT_STOPS: int = 0    # keep only non-stop legs

# Neither .dat file has a header row — column names supplied manually.
AIRPORT_COLS: list[str] = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "lat", "lon", "altitude", "timezone", "dst", "tz", "type", "source",
]
ROUTE_COLS: list[str] = [
    "airline", "airline_id", "source", "source_id",
    "destination", "destination_id", "codeshare", "stops", "equipment",
]

# Node attributes copied onto the graph from the airport table.
NODE_ATTRS: list[str] = ["name", "city", "country", "lat", "lon"]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_airports(path: Path = AIRPORTS_DAT) -> pd.DataFrame:
    """Load the raw OpenFlights airport table.

    Args:
        path: Path to ``airports.dat``.

    Returns:
        DataFrame with :data:`AIRPORT_COLS` columns; ``\\N`` parsed as NaN and
        ``lat``/``lon`` coerced to float.
    """
    df = pd.read_csv(path, header=None, names=AIRPORT_COLS, na_values=[NA_SENTINEL])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["iata"] = df["iata"].str.strip().str.upper()
    return df


def load_routes(path: Path = ROUTES_DAT) -> pd.DataFrame:
    """Load the raw OpenFlights route table.

    Args:
        path: Path to ``routes.dat``.

    Returns:
        DataFrame with :data:`ROUTE_COLS` columns; ``\\N`` parsed as NaN,
        ``stops`` coerced to numeric, endpoint codes upper-cased.
    """
    df = pd.read_csv(path, header=None, names=ROUTE_COLS, na_values=[NA_SENTINEL])
    df["stops"] = pd.to_numeric(df["stops"], errors="coerce")
    df["source"] = df["source"].str.strip().str.upper()
    df["destination"] = df["destination"].str.strip().str.upper()
    return df


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def filter_europe(airports: pd.DataFrame) -> pd.DataFrame:
    """Restrict airports to the European bounding box with a valid IATA code.

    Args:
        airports: Raw airport table from :func:`load_airports`.

    Returns:
        DataFrame indexed by IATA code, holding :data:`NODE_ATTRS`, one row per
        airport (duplicate IATA codes dropped, first kept).
    """
    in_lat = airports["lat"].between(*EUROPE_LAT)
    in_lon = airports["lon"].between(*EUROPE_LON)
    has_iata = airports["iata"].notna() & (airports["iata"].str.len() == IATA_CODE_LEN)

    eu = airports[in_lat & in_lon & has_iata].copy()
    eu = eu.drop_duplicates(subset="iata", keep="first").set_index("iata")
    return eu[NODE_ATTRS]


def filter_routes(routes: pd.DataFrame, valid_iata: set[str]) -> pd.DataFrame:
    """Keep only direct, non-codeshare routes between two European airports.

    Args:
        routes: Raw route table from :func:`load_routes`.
        valid_iata: Set of IATA codes considered "in Europe".

    Returns:
        Filtered copy of ``routes`` (self-loops removed).
    """
    mask = (
        (routes["stops"] == DIRECT_FLIGHT_STOPS)
        & (routes["codeshare"] != CODESHARE_FLAG)      # NaN != "Y" -> kept
        & routes["source"].isin(valid_iata)
        & routes["destination"].isin(valid_iata)
        & (routes["source"] != routes["destination"])  # guard against self-loops
    )
    return routes[mask].copy()


# --------------------------------------------------------------------------- #
# Graph construction (accepts a tidy edge frame, returns graph objects)
# --------------------------------------------------------------------------- #
def build_edge_list(routes_filtered: pd.DataFrame) -> pd.DataFrame:
    """Collapse filtered routes into a tidy weighted edge list.

    Weight = number of distinct operating carriers on the directed pair.

    Args:
        routes_filtered: Output of :func:`filter_routes`.

    Returns:
        DataFrame with columns ``source``, ``destination``, ``weight``.
    """
    return (
        routes_filtered
        .groupby(["source", "destination"])["airline"]
        .nunique()
        .reset_index(name="weight")
    )


def build_digraph(edges: pd.DataFrame, airports_eu: pd.DataFrame) -> nx.DiGraph:
    """Build the directed, weighted graph and attach airport metadata to nodes.

    Args:
        edges: Tidy edge list from :func:`build_edge_list`.
        airports_eu: IATA-indexed airport table from :func:`filter_europe`.

    Returns:
        Directed graph; each node carries :data:`NODE_ATTRS` attributes.
    """
    g = nx.from_pandas_edgelist(
        edges, "source", "destination", edge_attr="weight", create_using=nx.DiGraph
    )
    meta = airports_eu.reindex(list(g.nodes()))
    for attr in NODE_ATTRS:
        nx.set_node_attributes(g, meta[attr].to_dict(), attr)
    return g


def build_undirected(digraph: nx.DiGraph) -> nx.Graph:
    """Undirected projection: reciprocal edges collapsed, weights summed.

    Args:
        digraph: Directed graph from :func:`build_digraph`.

    Returns:
        Undirected graph carrying the same node attributes; edge ``weight`` is
        the sum of the two directional weights.
    """
    g = nx.Graph()
    g.add_nodes_from(digraph.nodes(data=True))
    for u, v, data in digraph.edges(data=True):
        w = data.get("weight", 1)
        if g.has_edge(u, v):
            g[u][v]["weight"] += w
        else:
            g.add_edge(u, v, weight=w)
    return g


def build_networks(
    airports_path: Path = AIRPORTS_DAT,
    routes_path: Path = ROUTES_DAT,
) -> tuple[nx.DiGraph, nx.Graph, pd.DataFrame, pd.DataFrame]:
    """Run the full pipeline: raw files -> both graph objects.

    Args:
        airports_path: Path to ``airports.dat``.
        routes_path: Path to ``routes.dat``.

    Returns:
        Tuple ``(digraph, undirected, edges, airports_eu)``.
    """
    airports_eu = filter_europe(load_airports(airports_path))
    routes_eu = filter_routes(load_routes(routes_path), set(airports_eu.index))
    edges = build_edge_list(routes_eu)
    digraph = build_digraph(edges, airports_eu)
    undirected = build_undirected(digraph)
    return digraph, undirected, edges, airports_eu


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
def graph_summary(graph: nx.Graph) -> dict[str, object]:
    """Compute headline statistics for a graph (directed or undirected).

    Args:
        graph: Any NetworkX graph.

    Returns:
        Dict with node/edge counts, density, component count, and the size of
        the largest (weakly, if directed) connected component.
    """
    if graph.is_directed():
        components = list(nx.weakly_connected_components(graph))
    else:
        components = list(nx.connected_components(graph))
    n = graph.number_of_nodes()
    largest = max((len(c) for c in components), default=0)
    return {
        "directed": graph.is_directed(),
        "nodes": n,
        "edges": graph.number_of_edges(),
        "density": round(nx.density(graph), 5),
        "n_components": len(components),
        "largest_cc_nodes": largest,
        "largest_cc_frac": round(largest / n, 4) if n else 0.0,
    }


if __name__ == "__main__":
    dg, ug, edge_df, apts = build_networks()
    print(f"European airports in bounding box (with IATA): {len(apts)}")
    print(f"Directed edges (operating routes)            : {dg.number_of_edges()}")
    for label, graph in [("DiGraph (directed)", dg), ("Undirected projection", ug)]:
        print(f"\n{label}")
        for key, value in graph_summary(graph).items():
            print(f"  {key:18}: {value}")