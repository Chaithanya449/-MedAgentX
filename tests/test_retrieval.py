"""
test_retrieval.py
------------------
Tests for the RAG pipeline: cleaning, chunking, and retrieval quality.

Most tests use a lightweight FakeEmbeddingModel (deterministic bag-of-words
hashing) so they run fast and offline, without downloading real model
weights. A small set of tests marked `@pytest.mark.integration` exercise
the real sentence-transformers model + FAISS end-to-end and are skipped
by default unless RUN_INTEGRATION_TESTS=1 is set, since they require
network access / model downloads.
"""

from __future__ import annotations

import os
import re
import numpy as np
import pytest

from app.rag.clean import clean_text
from app.rag.chunker import chunk_document, Chunk
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever


# ----------------------------------------------------------------------
# Fake embedding model: deterministic, offline, no dependencies.
# Encodes text as a normalized bag-of-words hashed vector so that
# semantically overlapping texts (shared words) score higher similarity,
# which is enough to test retrieval *logic* without a real model.
# ----------------------------------------------------------------------
class FakeEmbeddingModel:
    def __init__(self, dimension: int = 64):
        self.dimension = dimension

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = re.findall(r"[a-z0-9]+", text.lower())
        for w in words:
            idx = hash(w) % self.dimension
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_texts(self, texts, **kwargs) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        return np.stack([self._embed_one(t) for t in texts])

    def embed_query(self, query: str) -> np.ndarray:
        return self._embed_one(query)


# ----------------------------------------------------------------------
# clean_text tests
# ----------------------------------------------------------------------
class TestCleanText:
    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_removes_page_numbers(self):
        raw = "Intro text.\n\nPage 3 of 10\n\nMore content here."
        cleaned = clean_text(raw)
        assert "Page 3 of 10" not in cleaned
        assert "Intro text." in cleaned
        assert "More content here." in cleaned

    def test_removes_boilerplate_lines(self):
        raw = "Clinical guidance.\nAll Rights Reserved.\nDosage: 500mg."
        cleaned = clean_text(raw)
        assert "rights reserved" not in cleaned.lower()
        assert "Dosage: 500mg." in cleaned

    def test_dehyphenates_line_breaks(self):
        raw = "The patient has hyper-\ntension and needs treatment."
        cleaned = clean_text(raw)
        assert "hypertension" in cleaned

    def test_normalizes_whitespace(self):
        raw = "Too    many     spaces.\n\n\n\nToo many blank lines."
        cleaned = clean_text(raw)
        assert "Too    many" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_preserves_medical_units_and_symbols(self):
        raw = "Administer 5\u00b5g/kg IV, target temperature 37\u00b0C \u00b1 0.5."
        cleaned = clean_text(raw)
        assert "\u00b5g/kg" in cleaned
        assert "\u00b0C" in cleaned

    def test_does_not_alter_numeric_dosages(self):
        raw = "Prescribe 500mg amoxicillin three times daily for 7 days."
        cleaned = clean_text(raw)
        assert "500mg" in cleaned
        assert "7 days" in cleaned


# ----------------------------------------------------------------------
# chunk_document tests
# ----------------------------------------------------------------------
class TestChunkDocument:
    def test_empty_text_returns_no_chunks(self):
        assert chunk_document("", source_id="src1") == []

    def test_short_text_single_chunk(self):
        text = "Hypertension is high blood pressure. It increases stroke risk."
        chunks = chunk_document(text, source_id="src1", chunk_size=800, chunk_overlap=100)
        assert len(chunks) == 1
        assert chunks[0].source_id == "src1"
        assert chunks[0].chunk_id == "src1::chunk_0000"

    def test_long_text_produces_multiple_chunks(self):
        paragraph = "Diabetes management requires careful monitoring. " * 40
        text = "\n\n".join([paragraph] * 5)
        chunks = chunk_document(text, source_id="src2", chunk_size=500, chunk_overlap=100)
        assert len(chunks) > 1
        # positions should be sequential starting at 0
        assert [c.position for c in chunks] == list(range(len(chunks)))

    def test_chunks_respect_overlap_smaller_than_size(self):
        with pytest.raises(ValueError):
            chunk_document("some text", source_id="src3", chunk_size=100, chunk_overlap=100)

    def test_metadata_propagated_to_all_chunks(self):
        text = "Statement one. " * 100
        meta = {"title": "Test Doc", "license": "CC-BY-4.0"}
        chunks = chunk_document(text, source_id="src4", chunk_size=200, chunk_overlap=50, extra_metadata=meta)
        assert len(chunks) > 1
        for c in chunks:
            assert c.metadata["title"] == "Test Doc"
            assert c.metadata["license"] == "CC-BY-4.0"

    def test_no_chunk_is_empty(self):
        text = "First idea here.\n\nSecond idea here.\n\n\n\nThird idea, after extra blank lines."
        chunks = chunk_document(text, source_id="src5", chunk_size=40, chunk_overlap=10)
        assert all(c.text.strip() for c in chunks)


# ----------------------------------------------------------------------
# VectorStore + Retriever tests (using FakeEmbeddingModel)
# ----------------------------------------------------------------------
@pytest.fixture
def sample_corpus():
    return [
        ("doc_hypertension", "Hypertension is high blood pressure that increases the risk of heart disease and stroke.", {"specialty": ["cardiology"]}),
        ("doc_diabetes", "Type 2 diabetes is a chronic condition affecting how the body processes blood sugar glucose.", {"specialty": ["endocrinology"]}),
        ("doc_asthma", "Asthma is a respiratory condition causing airway inflammation and difficulty breathing.", {"specialty": ["pulmonology"]}),
        ("doc_hypertension_treatment", "Treatment for high blood pressure includes lifestyle changes and antihypertensive medication.", {"specialty": ["cardiology"]}),
    ]


@pytest.fixture
def populated_store(sample_corpus):
    embedder = FakeEmbeddingModel(dimension=64)
    store = VectorStore(dimension=64)

    texts = [text for _, text, _ in sample_corpus]
    embeddings = embedder.embed_texts(texts)
    metadata = [
        {
            "chunk_id": f"{source_id}::chunk_0000",
            "source_id": source_id,
            "text": text,
            "position": 0,
            "metadata": meta,
        }
        for source_id, text, meta in sample_corpus
    ]
    store.build(embeddings, metadata)
    return store, embedder


class TestVectorStore:
    def test_build_and_length(self, populated_store):
        store, _ = populated_store
        assert len(store) == 4

    def test_search_returns_requested_top_k(self, populated_store):
        store, embedder = populated_store
        query_vec = embedder.embed_query("blood pressure treatment")
        results = store.search(query_vec, top_k=2)
        assert len(results) == 2

    def test_search_empty_store_returns_empty_list(self):
        store = VectorStore(dimension=64)
        results = store.search(np.zeros(64, dtype=np.float32), top_k=3)
        assert results == []

    def test_save_and_load_roundtrip(self, populated_store, tmp_path):
        store, _ = populated_store
        save_dir = str(tmp_path / "vector_store")
        store.save(save_dir)

        loaded = VectorStore.load(save_dir)
        assert len(loaded) == len(store)
        assert loaded.metadata[0]["source_id"] == store.metadata[0]["source_id"]

    def test_load_missing_directory_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VectorStore.load(str(tmp_path / "does_not_exist"))


class TestRetriever:
    def test_relevant_result_ranked_first(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder, default_top_k=2)
        results = retriever.retrieve("high blood pressure")
        assert len(results) > 0
        top_source_ids = {r["source_id"] for r in results}
        assert "doc_hypertension" in top_source_ids or "doc_hypertension_treatment" in top_source_ids

    def test_empty_query_returns_no_results(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        assert retriever.retrieve("") == []
        assert retriever.retrieve("   ") == []

    def test_top_k_is_respected(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        results = retriever.retrieve("medical condition", top_k=1)
        assert len(results) == 1

    def test_results_sorted_by_score_descending(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        results = retriever.retrieve("diabetes blood sugar", top_k=4)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_source_filter_restricts_results(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        results = retriever.retrieve(
            "medical condition", top_k=4, source_filter=["doc_asthma"]
        )
        assert all(r["source_id"] == "doc_asthma" for r in results)

    def test_metadata_filter_restricts_by_specialty(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        results = retriever.retrieve(
            "condition",
            top_k=4,
            metadata_filter=lambda m: "cardiology" in m.get("specialty", []),
        )
        assert all("cardiology" in r["metadata"].get("specialty", []) for r in results)

    def test_min_score_threshold_filters_weak_matches(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        results = retriever.retrieve("asthma respiratory airway", top_k=4, min_score=0.99)
        # Only near-identical text should pass an extremely high threshold.
        assert all(r["score"] >= 0.99 for r in results)

    def test_retrieve_with_context_formats_citations(self, populated_store):
        store, embedder = populated_store
        retriever = Retriever(store, embedder)
        context = retriever.retrieve_with_context("blood pressure", top_k=1)
        assert context.startswith("[")
        assert "]" in context


# ----------------------------------------------------------------------
# Integration tests: real embedding model + real FAISS end-to-end.
# Skipped by default (require network access to download model weights).
# Run explicitly with: RUN_INTEGRATION_TESTS=1 pytest tests/test_retrieval.py
# ----------------------------------------------------------------------
@pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION_TESTS") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 to run tests requiring the real embedding model.",
)
class TestRetrievalIntegration:
    def test_end_to_end_retrieval_quality(self):
        from app.rag.embeddings import EmbeddingModel

        embedder = EmbeddingModel()
        corpus = [
            "Hypertension is high blood pressure that raises cardiovascular risk.",
            "Type 2 diabetes affects how the body regulates blood glucose.",
            "Asthma causes airway inflammation and shortness of breath.",
        ]
        embeddings = embedder.embed_texts(corpus)
        metadata = [
            {"chunk_id": f"c{i}", "source_id": f"s{i}", "text": t, "position": 0, "metadata": {}}
            for i, t in enumerate(corpus)
        ]
        store = VectorStore(dimension=embeddings.shape[1])
        store.build(embeddings, metadata)

        retriever = Retriever(store, embedder)
        results = retriever.retrieve("What raises the risk of heart disease?", top_k=1)
        assert len(results) == 1
        assert "blood pressure" in results[0]["text"].lower()