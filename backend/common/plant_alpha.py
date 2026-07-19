"""Shared fixture data for the "Plant Alpha" synthetic demo narrative.

Every synthetic document (#4) and the demo script (#33) should import this
instead of hardcoding equipment tags, so the story stays consistent across
ingestion, the knowledge graph, and the UI.
"""

PLANT_NAME = "Plant Alpha"

EQUIPMENT = [
    {"tag": "P-101", "name": "Feed Pump", "type": "Centrifugal Pump", "area": "Process Area A"},
    {"tag": "P-102", "name": "Backup Feed Pump", "type": "Centrifugal Pump", "area": "Process Area A"},
    {"tag": "T-201", "name": "Crude Feed Tank", "type": "Storage Tank", "area": "Tank Farm"},
    {"tag": "V-301", "name": "Feed Line Relief Valve", "type": "Pressure Relief Valve", "area": "Process Area A"},
    {"tag": "HX-401", "name": "Feed Preheater", "type": "Shell & Tube Heat Exchanger", "area": "Utilities Area"},
    {"tag": "C-501", "name": "Instrument Air Compressor", "type": "Reciprocating Compressor", "area": "Utilities Area"},
]

AREAS = ["Process Area A", "Tank Farm", "Utilities Area"]
