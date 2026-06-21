from difflib import SequenceMatcher
import re
import unicodedata

from flask import current_app


class VectorStoreService:
    _model = None
    _client = None

    def __init__(self):
        import chromadb

        if VectorStoreService._client is None:
            VectorStoreService._client = chromadb.PersistentClient(path=current_app.config["VECTORSTORE_PATH"])
        self.client = VectorStoreService._client

    @classmethod
    def embedding_model(cls):
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as exc:
                raise ValueError(
                    "SentenceTransformers/Torch is not available. Install Microsoft Visual C++ Redistributable "
                    "and verify the sentence-transformers installation."
                ) from exc
            cls._model = SentenceTransformer(current_app.config["EMBEDDING_MODEL"])
        return cls._model

    def collection(self, course_id):
        return self.client.get_or_create_collection(name=f"course_{course_id}")

    def add_chunks(self, course_id, chunks):
        if not chunks:
            return
        model = self.embedding_model()
        texts = [chunk["text"] for chunk in chunks]
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()
        collection = self.collection(course_id)
        collection.upsert(
            ids=[chunk["chroma_id"] for chunk in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "course_id": course_id,
                    "document_id": chunk["document_id"],
                    "source_file": chunk["source_file"],
                    "page_number": chunk["page_number"] or 0,
                    "chunk_id": chunk["chunk_id"],
                }
                for chunk in chunks
            ],
        )

    def query(self, course_id, query_text, top_k=5):
        collection = self.collection(course_id)
        count = collection.count()
        if count == 0:
            return []

        lexical_results = self._lexical_query(collection, query_text, top_k)
        query_embedding = self.embedding_model().encode([query_text], normalize_embeddings=True).tolist()[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        semantic_results = [
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
        combined = []
        seen = set()
        for item in lexical_results + semantic_results:
            identity = item["metadata"].get("chunk_id") or item["text"]
            if identity in seen:
                continue
            seen.add(identity)
            combined.append(item)
            if len(combined) == top_k:
                break
        return combined

    @staticmethod
    def _tokens(text):
        normalized = unicodedata.normalize("NFC", (text or "").casefold())
        return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)

    @classmethod
    def _lexical_score(cls, query_text, document):
        query_tokens = cls._tokens(query_text)
        document_tokens = cls._tokens(document)
        if not query_tokens or not document_tokens:
            return 0

        normalized_query = " ".join(query_tokens)
        normalized_document = " ".join(document_tokens)
        if normalized_query in normalized_document:
            return 1

        best_matches = [
            max(SequenceMatcher(None, query_token, document_token).ratio() for document_token in document_tokens)
            for query_token in query_tokens
        ]
        return sum(best_matches) / len(best_matches)

    @classmethod
    def _lexical_query(cls, collection, query_text, top_k):
        stored = collection.get(
            limit=min(collection.count(), 5000),
            include=["documents", "metadatas"],
        )
        candidates = []
        for document, metadata in zip(
            stored.get("documents", []),
            stored.get("metadatas", []),
        ):
            score = cls._lexical_score(query_text, document)
            if score >= 0.55:
                candidates.append(
                    {
                        "text": document,
                        "metadata": metadata,
                        "distance": None,
                        "lexical_score": score,
                    }
                )
        candidates.sort(key=lambda item: item["lexical_score"], reverse=True)
        return candidates[:top_k]
