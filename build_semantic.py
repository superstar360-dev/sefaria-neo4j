from config import SIM_THRESHOLD, USE_FAISS, MIN_LENGTH, EMBED_MODEL
from embed_models import get_embedder
from neo4j_io import driver, create_inferred_edge
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import faiss

def build():
    print(f"\n?? Starting Semantic Linker")
    print(f"?? Threshold: {SIM_THRESHOLD}, Min Length: {MIN_LENGTH}, Model: {EMBED_MODEL}")
    
    with driver.session() as sess:
        records = sess.run("""
            MATCH (t:Text)
            WHERE t.content_he IS NOT NULL
            RETURN t.id AS id, t.content_he AS text
        """)
        all_data = [(r["id"], r["text"]) for r in records]
    
    print(f"?? Total texts loaded: {len(all_data)}")
    
    # Filter by text length
    filtered = [(r, t) for r, t in all_data if len(t) >= MIN_LENGTH]
    if not filtered:
        print("? No texts meet the minimum length requirement.")
        return
    
    ids, corpus = zip(*filtered)
    print(f"? Filtered texts (len = {MIN_LENGTH}): {len(ids)}, Filtered:{len(filtered)}")

    # Generate embeddings
    embed = get_embedder()
    print("?? Generating embeddings...")
    embs = embed(list(corpus))
    print(f"? Generated {len(embs)} embeddings")

    pairs = []

    if USE_FAISS:
        print("? Using FAISS for similarity search...")
        dim = embs.shape[1]
        idx = faiss.IndexFlatL2(dim)
        idx.add(embs)
        D, I = idx.search(embs, k=10)

        for i in range(len(ids)):
            for k, j in enumerate(I[i]):
                if i < j:
                    score = 1 - D[i][k] / 2
                    if score >= SIM_THRESHOLD:
                        print(f"?? FAISS match: {ids[i]} ? {ids[j]} (score={score:.3f})")
                        pairs.append((ids[i], ids[j], score))
    else:
        print("?? Using Scikit cosine similarity...")
        sims = cosine_similarity(embs)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                score = sims[i][j]
                if score >= SIM_THRESHOLD:
                    print(f"?? Match: {ids[i]} ? {ids[j]} (score={score:.3f})")
                    pairs.append((ids[i], ids[j], score))

    if not pairs:
        print("?? No semantic matches above threshold.")
        return

    print(f"?? Writing {len(pairs)} inferred edges to Neo4j...")
    for src, tgt, score in pairs:
        with driver.session() as sess:
            sess.write_transaction(create_inferred_edge, src, tgt, score, EMBED_MODEL)

    print("? Semantic inference complete.\n")
