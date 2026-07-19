from rag.confidence import score_confidence


def test_empty_chunks_yields_zero_confidence():
    assert score_confidence([]) == 0.0


def test_averages_top_n_scores():
    chunks = [{"score": 0.9}, {"score": 0.8}, {"score": 0.7}, {"score": 0.1}]
    assert abs(score_confidence(chunks, top_n=3) - 0.8) < 1e-9


def test_lower_average_scores_yield_lower_confidence():
    in_corpus = [{"score": 0.79}, {"score": 0.76}, {"score": 0.7}]
    out_of_corpus = [{"score": 0.2}, {"score": 0.15}, {"score": 0.1}]
    assert score_confidence(out_of_corpus) < score_confidence(in_corpus)
