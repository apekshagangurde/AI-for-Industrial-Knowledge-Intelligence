# Knowledge Graph Schema

Locks the shape ingestion (#12, #13) and query code (#16) build against. Neo4j 5, local via
`docker compose up -d` (see `docker-compose.yml`) or Aura Free tier.

## Node labels

### `Equipment`
One per physical asset. Seeded from the "Plant Alpha" fixture (`backend/common/plant_alpha.py`);
extended by whatever equipment tags entity extraction (#12) finds in ingested text.

| Property | Type | Notes |
|---|---|---|
| `tag` | string | **unique key**, e.g. `P-101` |
| `name` | string | e.g. `Feed Pump` |
| `type` | string | e.g. `Centrifugal Pump` |
| `area` | string | denormalized copy of the linked `Area.name`, for quick filtering without a traversal |

### `Document`
One per ingested file (every `doc_type` in `data/raw/manifest.csv` / `data/synthetic/manifest.csv`).
`Procedure`, `Regulation`, and `Incident` below are dual-labeled with `Document` when they
originate from an actual ingested file, so a generic `(:Document)` match still finds them.

| Property | Type | Notes |
|---|---|---|
| `doc_id` | string | **unique key** — matches the `doc_id` chunker.py/embed_store.py already use |
| `title` | string | |
| `doc_type` | string | `regulation` \| `procedure` \| `incident` \| `incident_report` \| `om_manual` \| `inspection_report` \| `work_order` \| `pid_drawing` |
| `source_path` | string | relative path under `data/` |

### `Procedure`
Dual-labeled `:Document:Procedure` for every `doc_type = "procedure"` document (SOPs).

| Property | Type | Notes |
|---|---|---|
| `proc_id` | string | **unique key**, same value as `doc_id` |
| `title` | string | |

### `Regulation`
Two sources: (a) dual-labeled `:Document:Regulation` for whole-regulation source documents
(`doc_type = "regulation"`), and (b) standalone `Regulation` nodes created purely from a
`regulation_refs` mention inside another document's text (e.g. a work order citing
"OSHA 1910.119") — these may have no `Document` label at all if the regulation itself was never
separately ingested.

| Property | Type | Notes |
|---|---|---|
| `code` | string | **unique key**, e.g. `OSHA-3132`, `Factories Act 1948 S.21` |
| `title` | string | optional, human-readable name |

### `Incident`
Dual-labeled `:Document:Incident` for every `doc_type = "incident"` document.

| Property | Type | Notes |
|---|---|---|
| `incident_id` | string | **unique key**, same value as `doc_id` |
| `title` | string | |
| `date` | string (ISO date) | from the source manifest |

### `Person`
Extracted from text (work order technicians, inspection signoffs, incident reporters). Name
collisions across different real people are a known limitation, acceptable at hackathon scope
since "Plant Alpha" is a small synthetic cast.

| Property | Type | Notes |
|---|---|---|
| `name` | string | **unique key** |

### `Area`
Not in the original README node list, added here because `backend/common/plant_alpha.py`
already models plant areas as a fixed fixture (`AREAS`) and the `LOCATED_IN` relationship below
needs something to point at.

| Property | Type | Notes |
|---|---|---|
| `name` | string | **unique key**, e.g. `Process Area A` |

## Relationships

| Type | Direction | Meaning |
|---|---|---|
| `REFERENCES` | `(Document)-[:REFERENCES]->(Equipment \| Regulation \| Person)` | the document mentions this entity |
| `MAINTAINS` | `(Person)-[:MAINTAINS]->(Equipment)` | a person performed maintenance on this equipment (from a work order's personnel + equipment_tags) |
| `GOVERNED_BY` | `(Equipment)-[:GOVERNED_BY]->(Regulation)` | this equipment is subject to this regulation |
| `REPORTED_BY` | `(Incident)-[:REPORTED_BY]->(Person)` | who filed/reported the incident |
| `PART_OF` | `(Equipment)-[:PART_OF]->(Equipment)` | sub-component relationship (e.g. a seal `PART_OF` a pump) — expected to be rare in the seed corpus but supported |
| `LOCATED_IN` | `(Equipment)-[:LOCATED_IN]->(Area)` | equipment's physical location |

## Example subgraph (Plant Alpha's P-101 story)

```
(:Equipment {tag:"P-101"})-[:LOCATED_IN]->(:Area {name:"Process Area A"})
(:Document:Incident {incident_id:"2024-06-15_p-101-near-miss-june-2024"})
  -[:REFERENCES]->(:Equipment {tag:"P-101"})
(:Document:Incident {incident_id:"2024-11-25_p-101-mechanical-seal-failure-nov-2024"})
  -[:REFERENCES]->(:Equipment {tag:"P-101"})
(:Equipment {tag:"P-101"})-[:GOVERNED_BY]->(:Regulation {code:"OSHA-3132"})
(:Document:Procedure {proc_id:"2023-02-15_centrifugal-pump-operation"})
  -[:REFERENCES]->(:Equipment {tag:"P-101"})
```

This is exactly the shape #16 (KG-aware query expansion) needs: given "P-101" mentioned in a
user question, one traversal from the `Equipment` node surfaces every linked incident,
procedure, and regulation to boost/filter vector retrieval.

## Constraints

See `scripts/kg_constraints.cypher` — uniqueness constraints for every node label's key
property above. Run with:

```bash
cat scripts/kg_constraints.cypher | docker exec -i industrial-ki-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD"
```
