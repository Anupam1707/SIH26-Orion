-- =============================================================================
-- Module 5 — Aura Export Queries
-- =============================================================================
-- Run these in Neo4j Aura Browser to export fresh input CSVs for the
-- anomaly detection scripts.
--
-- IMPORTANT: Aura stores date/time fields as plain strings (not native
-- datetime types). See project log Section 6 for the fix pattern.
-- =============================================================================


-- =============================================================================
-- 1. EGONET DATA  →  intelligence/data/inputs/egonet_data.csv
--    Used by: anomaly_detection/oddball.py (OddBall structural scoring)
-- =============================================================================
-- For each Account, measure its egonet:
--   egonet_nodes = count of distinct neighbours
--   egonet_edges = count of TRANSACTED relationships *between* neighbours
-- Also pulls pagerank_score and community_id written by Module 4 analytics.

MATCH (a:Account)
OPTIONAL MATCH (a)-[:TRANSACTED]-(nbr:Account)
WITH a, collect(DISTINCT nbr) AS neighbours
OPTIONAL MATCH (n1:Account)-[:TRANSACTED]->(n2:Account)
WHERE n1 IN neighbours AND n2 IN neighbours
WITH a,
     size(neighbours)  AS egonet_nodes,
     count(DISTINCT n1) AS egonet_edges,
     coalesce(a.in_degree, 0)   AS in_deg,
     coalesce(a.out_degree, 0)  AS out_deg,
     coalesce(a.in_volume, 0)   AS in_volume,
     coalesce(a.out_volume, 0)  AS out_volume,
     a.pagerank_score            AS pagerank,
     a.community_id              AS community
RETURN a.account_id AS account_id,
       in_deg, out_deg, in_volume, out_volume,
       egonet_nodes, egonet_edges,
       pagerank, community
ORDER BY account_id


-- =============================================================================
-- 2. TEMPORAL DATA  →  intelligence/data/inputs/temporal_data.csv
--    Used by: anomaly_detection/temporal.py (temporal burst scoring)
-- =============================================================================
-- Collect all transaction timestamps and amounts per account.
-- Filter to accounts with ≥5 transactions (need enough points for burst window).
-- NOTE: toString() is required because timestamps are stored as plain strings,
--       not native Neo4j datetimes — do not use datetime() here.

MATCH (a:Account)-[t:TRANSACTED]->()
WITH a.account_id AS account_id,
     count(t) AS tx_count,
     collect(toString(t.timestamp)) AS timestamps,
     collect(t.amount) AS amounts
WHERE tx_count >= 5
RETURN account_id, tx_count, timestamps, amounts
ORDER BY account_id


-- =============================================================================
-- 3. VALIDATION CHECK — confirm planted patterns are in the graph
--    (Run ad-hoc; not an input to any script)
-- =============================================================================

-- Mule fan-in: 12 feeders → A00013 → A00014
MATCH (feeder:Account)-[t:TRANSACTED]->(collector:Account {account_id:'A00013'})
WITH collector, count(DISTINCT feeder) AS feeder_count,
     min(datetime(replace(t.timestamp,' ','T'))) AS first_in,
     max(datetime(replace(t.timestamp,' ','T'))) AS last_in
MATCH (collector)-[fwd:TRANSACTED]->(target:Account {account_id:'A00014'})
RETURN feeder_count, first_in, last_in,
       fwd.amount AS forwarded_amount,
       datetime(replace(fwd.timestamp,' ','T')) AS forward_time

-- Scatter source A00055: fans out to 8 receivers
MATCH (src:Account {account_id:'A00055'})-[t:TRANSACTED]->(rcv:Account)
RETURN rcv.account_id AS receiver,
       t.amount AS amount,
       t.timestamp AS ts
ORDER BY ts

-- Structuring ring: A00069–A00074 in ₹9,000–9,900 band
MATCH (a:Account)-[t:TRANSACTED]->()
WHERE a.account_id IN ['A00069','A00070','A00071','A00072','A00073','A00074']
  AND toFloat(t.amount) >= 9000
  AND toFloat(t.amount) <= 9900
RETURN a.account_id,
       count(t) AS suspicious_tx,
       min(t.timestamp) AS first,
       max(t.timestamp) AS last
ORDER BY a.account_id
