// ==============================================================================
// MuleTrail / SIH26 — Problem Statement 26184: Demo Knowledge Graph
// Forecast Likely Cash Withdrawal Locations in Advance (MHA / I4C)
//
// Topology:
//   8 Victims -> 5 L1 Mules -> 2 Collectors (L2) -> 3 L3 Mules -> 6 Past ATMs
//                                                \-> 2 Predicted ATMs (P1, P2)
//   Caller K1 -> SIM-A (deactivated) -[:REPLACED_BY]-> SIM-B (new)
//   5 Citizens (Background Noise)
//   Districts: Nuh, Gurugram, Palwal, Mathura, Faridabad
//
// All demo nodes are tagged with {demo: true} for safe isolation.
// ==============================================================================

// ------------------------------------------------------------------------------
// Step 1: Clean up existing demo nodes (Idempotent execution)
// ------------------------------------------------------------------------------
MATCH (n {demo: true})
DETACH DELETE n;

// ------------------------------------------------------------------------------
// Step 2: Create Entities
// ------------------------------------------------------------------------------

// 2.1 Victims (V1 to V8)
UNWIND range(1, 8) AS i
CREATE (:Victim {id: 'V' + i, name: 'Victim ' + i, demo: true});

// 2.2 Mule Accounts (L1 and L3)
UNWIND [
  {id: 'M1', layer: 1}, {id: 'M2', layer: 1}, {id: 'M3', layer: 1}, {id: 'M4', layer: 1}, {id: 'M5', layer: 1},
  {id: 'M6', layer: 3}, {id: 'M7', layer: 3}, {id: 'M8', layer: 3}
] AS m
CREATE (:Mule {
  id: m.id, 
  name: 'Mule ' + m.id + ' (L' + toString(m.layer) + ')', 
  layer: m.layer, 
  demo: true
});

// 2.3 Collectors (L2 Hubs)
CREATE
  (:Collector {id: 'C1', name: 'Collector C1 (L2)', layer: 2, demo: true}),
  (:Collector {id: 'C2', name: 'Collector C2 (L2)', layer: 2, demo: true});

// 2.4 Legitimate Citizens (Background Noise)
UNWIND range(1, 5) AS i
CREATE (:Citizen {id: 'N' + i, name: 'Citizen ' + i, demo: true});

// 2.5 Caller & SIM Card Rotation
CREATE
  (k:Caller {id: 'K1', name: 'Caller K1', demo: true}),
  (s1:SIM {id: 'SIM-A', name: 'SIM-A (deactivated)', demo: true}),
  (s2:SIM {id: 'SIM-B', name: 'SIM-B (new)', demo: true}),
  (k)-[:USES]->(s1),
  (k)-[:USES]->(s2),
  (s1)-[:REPLACED_BY {gap_hours: 20}]->(s2);

// 2.6 Historical ATMs and Administrative Districts
UNWIND [
  {id: 'A1', name: 'ATM Nuh-1', lat: 28.10, lon: 77.00, d: 'Nuh'},
  {id: 'A2', name: 'ATM Nuh-2', lat: 28.11, lon: 77.02, d: 'Nuh'},
  {id: 'A3', name: 'ATM Gurugram-5', lat: 28.46, lon: 77.03, d: 'Gurugram'},
  {id: 'A4', name: 'ATM Palwal-1', lat: 28.14, lon: 77.32, d: 'Palwal'},
  {id: 'A5', name: 'ATM Mathura-3', lat: 27.49, lon: 77.67, d: 'Mathura'},
  {id: 'A6', name: 'ATM Faridabad-2', lat: 28.41, lon: 77.31, d: 'Faridabad'}
] AS a
CREATE (atm:ATM {id: a.id, name: a.name, lat: a.lat, lon: a.lon, demo: true})
MERGE (d:District {name: a.d, demo: true})
CREATE (atm)-[:IN_DISTRICT]->(d);

// 2.7 Predicted Cash-Out Hotspot ATMs (Key Deliverable b)
UNWIND [
  {id: 'P1', name: 'ATM Palwal-2 (PREDICTED)', lat: 28.15, lon: 77.33, d: 'Palwal'},
  {id: 'P2', name: 'ATM Faridabad-7 (PREDICTED)', lat: 28.40, lon: 77.30, d: 'Faridabad'}
] AS p
CREATE (pa:PredictedATM {id: p.id, name: p.name, lat: p.lat, lon: p.lon, demo: true})
MERGE (d:District {name: p.d, demo: true})
CREATE (pa)-[:IN_DISTRICT]->(d);

// ------------------------------------------------------------------------------
// Step 3: Create Relationships & Flows
// ------------------------------------------------------------------------------

// 3.1 Vishing Calls: Victims receive calls from rotating SIMs
UNWIND [
  ['V1', 'SIM-A'], ['V2', 'SIM-A'], ['V3', 'SIM-A'], ['V4', 'SIM-A'],
  ['V5', 'SIM-B'], ['V6', 'SIM-B'], ['V7', 'SIM-B'], ['V8', 'SIM-B']
] AS c
MATCH (v:Victim {id: c[0], demo: true}), (s:SIM {id: c[1], demo: true})
CREATE (v)-[:CALLED {ts: datetime('2026-09-28T09:30:00')}]->(s);

// 3.2 Transactions: Victims -> L1 Mules -> Collectors (L2) -> L3 Mules + Structuring & Background Noise
UNWIND [
  // Victims -> L1 Mules
  ['V1', 'M1', 85000, 2],
  ['V2', 'M1', 120000, 15],
  ['V3', 'M2', 60000, 20],
  ['V4', 'M2', 45000, 28],
  ['V5', 'M3', 150000, 35],
  ['V6', 'M3', 72000, 50],
  ['V7', 'M4', 95000, 55],
  ['V8', 'M5', 110000, 62],

  // L1 Mules -> Collectors (~95-97% forwarded, Fan-in typology)
  ['M1', 'C1', 199000, 80],
  ['M2', 'C1', 102000, 85],
  ['M3', 'C2', 215000, 110],
  ['M4', 'C2', 92000, 115],
  ['M5', 'C2', 106000, 120],

  // Collectors -> L3 Mules (Layering typology)
  ['C1', 'M6', 295000, 150],
  ['C2', 'M7', 240000, 170],
  ['C2', 'M8', 160000, 175],

  // Structuring: Smurfing just under Rs 10,000 reporting threshold
  ['M8', 'M6', 9500, 200],
  ['M8', 'M6', 9400, 260],
  ['M8', 'M6', 9600, 320],

  // Normal Citizen Transactions (Background Noise)
  ['N1', 'N2', 500, 15],
  ['N2', 'N3', 1200, 90],
  ['N3', 'N4', 300, 200],
  ['N4', 'N5', 2000, 240],
  ['N5', 'N1', 800, 300],
  ['N1', 'N4', 150, 330]
] AS t
MATCH (a {id: t[0], demo: true}), (b {id: t[1], demo: true})
CREATE (a)-[:TRANSACTED {
  amount: t[2],
  ts: datetime('2026-09-28T10:00:00') + duration({minutes: t[3]})
}]->(b);

// 3.3 Historical Cash-Outs (Past withdrawals learned by models)
UNWIND [
  ['M6', 'A1', 50000, 0],
  ['M6', 'A2', 50000, 90],
  ['M6', 'A3', 40000, 300],
  ['M7', 'A5', 60000, 20],
  ['M7', 'A6', 45000, 180],
  ['M8', 'A2', 30000, 60],
  ['M8', 'A6', 35000, 240]
] AS w
MATCH (m:Mule {id: w[0], demo: true}), (a:ATM {id: w[1], demo: true})
CREATE (m)-[:WITHDREW_AT {
  amount: w[2],
  ts: datetime('2026-09-27T18:00:00') + duration({minutes: w[3]})
}]->(a);

// 3.4 Predictive Engine Outputs (ML Forecasted Cash-Out ATMs)
UNWIND [
  ['M6', 'P1', 0.87],
  ['M7', 'P2', 0.79],
  ['M8', 'P1', 0.64]
] AS r
MATCH (m:Mule {id: r[0], demo: true}), (p:PredictedATM {id: r[1], demo: true})
CREATE (m)-[:PREDICTED_CASHOUT {
  probability: r[2], 
  window: 'next 3 hours',
  confidence: 'High',
  model: 'Graph-Aware XGBoost + KDE'
}]->(p);

// ------------------------------------------------------------------------------
// Step 4: Display & Verification Queries
// ------------------------------------------------------------------------------

// Query A: Complete Demo Graph (39 Nodes, 50+ Edges)
// MATCH (n {demo: true})-[r]->(m)
// RETURN n, r, m;

// Query B: Clean End-to-End Fraud Chain (Presentation / Slide View)
// MATCH p=(v:Victim)-[:TRANSACTED*1..4]->(m:Mule)-[:PREDICTED_CASHOUT]->(pa:PredictedATM)
// RETURN p;
