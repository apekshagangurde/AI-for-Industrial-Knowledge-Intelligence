// Uniqueness constraints for the schema defined in docs/kg-schema.md.
// Idempotent (IF NOT EXISTS) — safe to re-run.
//
// Usage:
//   cat scripts/kg_constraints.cypher | docker exec -i industrial-ki-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD"

CREATE CONSTRAINT equipment_tag_unique IF NOT EXISTS
FOR (e:Equipment) REQUIRE e.tag IS UNIQUE;

CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.doc_id IS UNIQUE;

CREATE CONSTRAINT procedure_id_unique IF NOT EXISTS
FOR (p:Procedure) REQUIRE p.proc_id IS UNIQUE;

CREATE CONSTRAINT regulation_code_unique IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.code IS UNIQUE;

CREATE CONSTRAINT incident_id_unique IF NOT EXISTS
FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE;

CREATE CONSTRAINT person_name_unique IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT area_name_unique IF NOT EXISTS
FOR (a:Area) REQUIRE a.name IS UNIQUE;
