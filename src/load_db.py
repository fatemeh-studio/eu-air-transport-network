"""Load the European Air Transport Network into a SQLite database.

Builds the graph via :func:`build_graph.build_networks`, then materialises it as
two tables in ``network.db``:

    nodes  — one row per airport that carries intra-European service (the graph
             nodes, keyed by IATA). Static attributes are filled here; the
             centrality columns (in/out-degree, betweenness, closeness,
             eigenvector, PageRank) and the Louvain ``community`` column are
             created NULL and filled later by notebooks 02 and 03 with UPDATE
             statements — ``sql/schema.sql`` pre-declares them so no ALTER TABLE
             is ever needed.
    edges  — one row per directed (source -> destination) operating route;
             ``weight`` = number of distinct operating carriers on that pair
             (the directed edge list :func:`build_graph.build_networks` returns).

Table definitions live in ``sql/schema.sql`` (single source of truth). This
module executes that script, inserts the data, and round-trips it back out with
``pandas`` to prove the load succeeded.

WARNING — re-running this script REBUILDS the database from scratch: the schema
drops and recreates both tables, wiping any centrality/community values written
by later notebooks. Run it once up front; re-run only to reset, then re-run
notebooks 02/03.

Data vintage: OpenFlights June 2014 snapshot.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import networkx as nx
import pandas as pd

from build_graph import NODE_ATTRS, build_networks
from utils import DB_PATH, SCHEMA_PATH

# --------------------------------------------------------------------------- #
# Constants (no magic strings scattered through the code)
# --------------------------------------------------------------------------- #
NODES_TABLE: str = "nodes"
EDGES_TABLE: str = "edges"
EDGE_COLS: list[str] = ["source", "destination", "weight"]


# --------------------------------------------------------------------------- #
# Node frame (taken from the GRAPH, not the airport table)
# --------------------------------------------------------------------------- #
def nodes_frame(digraph: nx.DiGraph) -> pd.DataFrame:
    """Extract the node table from the directed graph.

    Node attributes are read off the graph rather than the filtered airport
    table on purpose: the bounding box holds ~1,000 EU airports, but only those
    that actually carry intra-European service become graph nodes. Sourcing from
    the graph guarantees the ``nodes`` table matches the graph exactly — one row
    per node, no isolated airfields.

    Args:
        digraph: Directed graph from :func:`build_graph.build_networks`.

    Returns:
        DataFrame with columns ``iata`` + :data:`build_graph.NODE_ATTRS`, one row
        per graph node.
    """
    records = [
        {"iata": iata, **{attr: data.get(attr) for attr in NODE_ATTRS}}
        for iata, data in digraph.nodes(data=True)
    ]
    return pd.DataFrame.from_records(records, columns=["iata", *NODE_ATTRS])


# --------------------------------------------------------------------------- #
# Schema + write
# --------------------------------------------------------------------------- #
def create_schema(conn: sqlite3.Connection, schema_path: Path = SCHEMA_PATH) -> None:
    """Create the ``nodes`` and ``edges`` tables from ``sql/schema.sql``.

    The script drops both tables first, so calling this on an existing database
    resets it to the empty structural state.

    Args:
        conn: Open SQLite connection (foreign keys already enabled).
        schema_path: Path to ``schema.sql``.
    """
    conn.executescript(schema_path.read_text(encoding="utf-8"))


def write_tables(
    conn: sqlite3.Connection,
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
) -> None:
    """Insert nodes, then edges, into the already-created tables.

    Nodes are written first so the edges' foreign keys resolve. Only the columns
    present in ``nodes_df`` are inserted; the centrality/community columns
    declared in the schema stay NULL for notebooks 02/03 to fill.

    Args:
        conn: Open SQLite connection with the schema already created.
        nodes_df: Output of :func:`nodes_frame`.
        edges_df: Directed edge list with ``source``, ``destination``, ``weight``.

    Raises:
        ValueError: If any edge endpoint is absent from the node set (which would
            violate the foreign key) — caught here to give a readable message
            instead of a raw ``IntegrityError``.
    """
    node_ids = set(nodes_df["iata"])
    endpoints = set(edges_df["source"]) | set(edges_df["destination"])
    orphans = endpoints - node_ids
    if orphans:
        raise ValueError(
            f"{len(orphans)} edge endpoint(s) absent from the nodes table: "
            f"{sorted(orphans)[:10]}"
        )

    nodes_df.to_sql(NODES_TABLE, conn, if_exists="append", index=False)
    edges_df[EDGE_COLS].to_sql(EDGES_TABLE, conn, if_exists="append", index=False)
    conn.commit()


# --------------------------------------------------------------------------- #
# Verification (pd.read_sql round-trip)
# --------------------------------------------------------------------------- #
def roundtrip_check(conn: sqlite3.Connection) -> dict[str, int]:
    """Read the tables back with pandas and collect sanity metrics.

    Args:
        conn: Open SQLite connection with data already written.

    Returns:
        Dict with node/edge row counts and how many nodes already have a
        non-NULL betweenness value — expected to be 0 immediately after load.
    """
    n_nodes = pd.read_sql(f"SELECT COUNT(*) AS n FROM {NODES_TABLE}", conn).at[0, "n"]
    n_edges = pd.read_sql(f"SELECT COUNT(*) AS n FROM {EDGES_TABLE}", conn).at[0, "n"]
    n_scored = pd.read_sql(
        f"SELECT COUNT(betweenness) AS n FROM {NODES_TABLE}", conn
    ).at[0, "n"]
    return {
        "nodes": int(n_nodes),
        "edges": int(n_edges),
        "nodes_with_betweenness": int(n_scored),
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def load_database(
    db_path: Path = DB_PATH,
    schema_path: Path = SCHEMA_PATH,
) -> dict[str, int]:
    """Build the network and load it into SQLite end-to-end.

    Args:
        db_path: Destination ``network.db`` (created / overwritten).
        schema_path: Path to ``schema.sql``.

    Returns:
        The metrics dict from :func:`roundtrip_check`.
    """
    digraph, _undirected, edges, _airports_eu = build_networks()
    nodes = nodes_frame(digraph)

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        create_schema(conn, schema_path)
        write_tables(conn, nodes, edges)
        metrics = roundtrip_check(conn)

    # Cross-check the round-trip against the in-memory graph.
    assert metrics["nodes"] == digraph.number_of_nodes(), "node count mismatch"
    assert metrics["edges"] == digraph.number_of_edges(), "edge count mismatch"
    return metrics


if __name__ == "__main__":
    result = load_database()
    print(f"Loaded {DB_PATH.name}")
    print(f"  nodes                : {result['nodes']}")
    print(f"  edges                : {result['edges']}")
    print(f"  nodes w/ betweenness : {result['nodes_with_betweenness']} (expect 0)")

    # Prove the round-trip returns real rows, not just counts.
    with closing(sqlite3.connect(DB_PATH)) as conn:
        vie = pd.read_sql(
            "SELECT iata, name, city, country FROM nodes WHERE iata = 'VIE'", conn
        )
        busiest = pd.read_sql(
            "SELECT source, destination, weight FROM edges "
            "ORDER BY weight DESC, source LIMIT 5",
            conn,
        )
    print("\nVienna row:")
    print(vie.to_string(index=False))
    print("\nTop 5 edges by operating-carrier weight:")
    print(busiest.to_string(index=False))