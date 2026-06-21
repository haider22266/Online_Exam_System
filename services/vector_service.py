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
        query_embedding = self.embedding_model().encode([query_text], normalize_embeddings=True).tolist()[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
