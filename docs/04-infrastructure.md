# Infrastructure Notes — Neo4j Aura

## Environment

- **Aura only** — no local Neo4j Desktop. Free tier.
- Connection details in `.env` (see `.env.example`)
- Confirmed schema via `db.labels()` / `db.relationshipTypes()`

---

## Node Labels in Aura

`Account`, `Person`, `PhoneNumber`, `Organization`, `Vehicle`, `Location`, `Event`,
`Case`, `Crime`, `Evidence`, `Document`, `Alias`, `Source`, `Observation`

## Key Relationship Types

`HOLDS_ACCOUNT`, `OWNS_PHONE`, `OWNS_VEHICLE`, `CALLED`, `TRANSACTED`, `MEMBER_OF`,
`PART_OF_CASE`, `SOURCED_FROM`, `ASSOCIATED_WITH`,
`SAME_ENTITY`, `DIFFERENT_ENTITY`, `UNCERTAIN_ENTITY`

---

## Critical Infrastructure Quirk — String vs Datetime

**Date/time fields in Aura are stored as plain strings, not native Neo4j datetime types.**

This caused multiple silent failures — queries returning empty results with no error.

Fields affected: `TRANSACTED.timestamp`, `Event.start_timestamp`, `PhoneNumber.activation_date`,
`PhoneNumber.deactivation_date`, and others.

### Fix patterns

```cypher
-- Full timestamp:
datetime(replace(field, ' ', 'T'))

-- Date only:
date(field)

-- NEVER do this (silently wrong):
field + duration('P2D')   -- evaluates to null inside WHERE, drops the row, no error
```

This bug was hit **twice**:
1. Several Module 4 queries returned empty until diagnosed via `valueType()` checks
2. Burner rotation pattern (PH00002/PH00001) silently dropped from the full candidate
   pipeline — `string + duration` produced null, WHERE discarded the row, no error thrown

**Recommended:** do a one-time audit of every date/time comparison in Module 5's Cypher.

---

## Aura GDS Session Limit

Free tier: **only 1 concurrent GDS session**.

- `gds.graph.drop()` removes a graph projection but does **NOT** release the session
- Repeated 429 errors until diagnosed
- `gds.session.list()` is the correct diagnostic (not `gds.graph.list()`)
- Explicit `gds.session.drop()`/`delete()` not available on free tier
- Stuck sessions clear automatically in ~10-15 minutes

---

## Aura GDS Projection Syntax

Free tier requires Cypher-projection form, not classic form:

```cypher
-- Correct (Cypher projection):
MATCH (src)-[r:TRANSACTED]->(tgt)
RETURN gds.graph.project('myGraph', src, tgt, {}, {memory: '2GB'})

-- Does NOT work on Aura free tier:
CALL gds.graph.project('myGraph', 'Account', 'TRANSACTED')
```

---

## Module 4 Properties Written Back to Aura

After running `graph/analytics/run_pagerank.py --write-back`, these properties are
available for Cypher queries in all other modules:

| Property | Node | Description |
|----------|------|-------------|
| `pagerank_score` | PhoneNumber, Account | PageRank centrality |
| `betweenness_score` | PhoneNumber | Betweenness centrality |
| `community_id` | varies | Louvain community membership |

Query example:
```cypher
MATCH (a:Account)
WHERE a.pagerank_score IS NOT NULL
RETURN a.account_id, a.pagerank_score, a.community_id
ORDER BY a.pagerank_score DESC
LIMIT 20
```
