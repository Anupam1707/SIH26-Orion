#!/usr/bin/env python3
"""
run_pagerank.py

CLI entry point to execute PageRank analysis on the Phone Communication Network.
Identifies influential communication hubs and key criminal suspects from CDRs.

Usage:
    python run_pagerank.py
    python run_pagerank.py --limit 25 --write-back
    python run_pagerank.py --export pagerank_results.csv
"""

import sys
import argparse
from pathlib import Path
from tabulate import tabulate
import pandas as pd
from loguru import logger

from graph.config import get_driver
from graph.analytics.pagerank import run_phone_pagerank_analysis


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run PageRank centrality analysis on Neo4j Phone Communication graph."
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="Number of top influential phone numbers to display (default: 20)."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.85,
        help="Damping factor for PageRank (default: 0.85)."
    )
    parser.add_argument(
        "--unweighted",
        action="store_true",
        help="Run unweighted PageRank (default: weighted by call frequency)."
    )
    parser.add_argument(
        "--write-back", "-w",
        action="store_true",
        help="Persist calculated pagerank_score, in_degree, out_degree back to Neo4j."
    )
    parser.add_argument(
        "--export", "-e",
        type=str,
        default=None,
        help="Path to export results as CSV (e.g. pagerank_top20.csv)."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("Initializing Neo4j connection...")
    driver = get_driver()

    try:
        results = run_phone_pagerank_analysis(
            driver=driver,
            top_n=args.limit,
            alpha=args.alpha,
            weighted=not args.unweighted,
            write_back=args.write_back
        )

        if not results:
            logger.warning("No results returned.")
            return

        # Format output table
        headers = [
            "Rank",
            "Phone ID",
            "PageRank",
            "In-Calls",
            "Out-Calls",
            "Total",
            "Provider",
            "Subscriber Name",
            "Owner Status"
        ]
        rows = [
            [
                r["rank"],
                r["phone_id"],
                f"{r['pagerank']:.6f}",
                r["in_degree"],
                r["out_degree"],
                r["total_calls"],
                r["service_provider"],
                r["owner_name"],
                r["owner_status"],
            ]
            for r in results
        ]

        print("\n" + "=" * 95)
        print(f" TOP {args.limit} INFLUENTIAL PHONE NUMBERS (PAGERANK CENTRALITY) ")
        print("=" * 95)
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
        print("=" * 95 + "\n")

        if args.export:
            df = pd.DataFrame(results)
            df.to_csv(args.export, index=False)
            logger.success(f"Exported top {len(results)} results to {args.export}")

    finally:
        driver.close()
        logger.info("Neo4j connection closed.")


if __name__ == "__main__":
    main()
