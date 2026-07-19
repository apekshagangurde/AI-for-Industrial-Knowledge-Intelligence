import sys

from ingestion import run_pipeline


def test_skip_graph_never_touches_graph_writer(monkeypatch, capsys):
    monkeypatch.setattr(
        "ingestion.embed_store.run_ingestion", lambda: {"documents": 3, "chunks": 10}
    )

    def fail_if_called():
        raise AssertionError("graph_writer.run_graph_ingestion should not be called with --skip-graph")

    monkeypatch.setattr("ingestion.graph_writer.run_graph_ingestion", lambda **kw: fail_if_called())
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--skip-graph"])

    run_pipeline.main()

    out = capsys.readouterr().out
    assert "Documents embedded:      3" in out
    assert "Chunks embedded:         10" in out
    assert "Documents graphed:       0" in out


def test_full_run_reports_both_summaries(monkeypatch, capsys):
    monkeypatch.setattr(
        "ingestion.embed_store.run_ingestion", lambda: {"documents": 24, "chunks": 192}
    )
    monkeypatch.setattr(
        "ingestion.graph_writer.run_graph_ingestion",
        lambda **kw: {"documents": 10, "equipment": 7, "persons": 4, "regulations": 30, "relationships": 43},
    )
    monkeypatch.setattr("ingestion.graph_writer.close_driver", lambda: None)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"])

    run_pipeline.main()

    out = capsys.readouterr().out
    assert "Documents embedded:      24" in out
    assert "Chunks embedded:         192" in out
    assert "Documents graphed:       10" in out
    assert "Equipment refs written:  7" in out
    assert "Relationships written:   43" in out
