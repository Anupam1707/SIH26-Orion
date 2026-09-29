"""Observed, time-filtered account multigraph."""
import networkx as nx
from app.data import Public


def build_graph(public: Public, clock) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for account in public.accounts.to_dict('records'):
        if account['opened_at'] <= clock:
            graph.add_node(account['id'], **account)
    for tx in public.tx_upto(clock).to_dict('records'):
        graph.add_edge(tx['src'], tx['dst'], key=tx['id'], **tx)
    return graph
