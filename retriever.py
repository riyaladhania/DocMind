
from ingest import model, client


def retrieve(question, k=4):

    # Get the uploaded document collection
    collection = client.get_collection("docs")

    # Convert question into an embedding
    q_vec = model.encode(question).tolist()

    # Search for the most relevant document chunks
    res = collection.query(
        query_embeddings=[q_vec],
        n_results=k
    )

    # Return text and complete source information
    results = []

    documents = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]

    for doc, meta in zip(documents, metadatas):

        results.append({
            "text": doc,
            "page": meta.get("page", 1),
            "location": meta.get("location", "Document"),
            "file_name": meta.get("file_name", ""),
            "file_type": meta.get("file_type", "")
        })

    return results
