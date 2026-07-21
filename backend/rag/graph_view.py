"""Knowledge-graph neighborhood for the visualization tab (#26).

Returns an equipment node's local graph (linked documents, incidents,
regulations, people, area) shaped for react-force-graph: {nodes, links}.
"""
from __future__ import annotations

from common.observability import observe
from rag.kg_expand import find_equipment_tags

# Node label -> color hint the frontend can use (kept here so backend + UI agree).
NODE_TYPES = {
    "Equipment": "#2563eb",
    "Document": "#64748b",
    "Incident": "#dc2626",
    "Regulation": "#16a34a",
    "Person": "#9333ea",
    "Procedure": "#0891b2",
    "Area": "#ca8a04",
}


def _primary_label(labels: list[str]) -> str:
    for label in ("Equipment", "Incident", "Regulation", "Procedure", "Person", "Area", "Document"):
        if label in labels:
            return label
    return labels[0] if labels else "Node"


def _node_key(node) -> str:
    props = dict(node)
    return props.get("tag") or props.get("doc_id") or props.get("code") or props.get("name") or str(node.id)


def _node_name(node, label: str) -> str:
    props = dict(node)
    return props.get("tag") or props.get("title") or props.get("name") or props.get("code") or label


@observe(name="graph.neighborhood")
def equipment_neighborhood(equipment_tag: str, hops: int = 1) -> dict:
    """Returns {center, nodes:[{id,name,type,color}], links:[{source,target,type}]}.

    Empty graph (not an error) if Neo4j is unavailable or the tag is unknown."""
    canonical = (find_equipment_tags(equipment_tag) or [equipment_tag])[0]
    try:
        from ingestion.graph_writer import get_driver

        driver = get_driver()
    except Exception:
        return {"center": canonical, "nodes": [], "links": []}

    nodes: dict[str, dict] = {}
    links: list[dict] = []
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (e:Equipment {tag: $tag})
                OPTIONAL MATCH path = (e)-[r*1..%d]-(n)
                RETURN e, relationships(path) AS rels, nodes(path) AS ns
                """
                % max(1, min(hops, 2)),
                tag=canonical,
            )
            for record in result:
                center = record["e"]
                ck = _node_key(center)
                nodes.setdefault(
                    ck, {"id": ck, "name": _node_name(center, "Equipment"), "type": "Equipment",
                         "color": NODE_TYPES["Equipment"]}
                )
                for node in record["ns"] or []:
                    label = _primary_label(list(node.labels))
                    key = _node_key(node)
                    nodes.setdefault(
                        key, {"id": key, "name": _node_name(node, label), "type": label,
                              "color": NODE_TYPES.get(label, "#94a3b8")}
                    )
                for rel in record["rels"] or []:
                    links.append(
                        {
                            "source": _node_key(rel.start_node),
                            "target": _node_key(rel.end_node),
                            "type": rel.type,
                        }
                    )
    except Exception:
        return {"center": canonical, "nodes": list(nodes.values()), "links": links}

    # De-dup links.
    seen = set()
    unique_links = []
    for link in links:
        sig = (link["source"], link["target"], link["type"])
        if sig not in seen:
            seen.add(sig)
            unique_links.append(link)

    return {"center": canonical, "nodes": list(nodes.values()), "links": unique_links}
