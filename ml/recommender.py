import numpy as np
import random
from ml.embeddings import load_embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)


def build_preference_vector(conn, user_id):
    ratings = conn.execute("""
                           SELECT a.embedding, r.rating
                           FROM article_ratings r
                                    JOIN articles a ON a.id = r.article_id
                           WHERE r.user_id = ?
                             AND a.embedding IS NOT NULL
                           """, (user_id,)).fetchall()

    if not ratings:
        return None

    positive = [load_embedding(blob) for blob, rating in ratings if rating == 1]
    negative = [load_embedding(blob) for blob, rating in ratings if rating == -1]

    dim = load_embedding(ratings[0][0]).shape[0]
    preference = np.zeros(dim)

    if positive:
        preference += np.mean(positive, axis=0)

    if negative:
        preference -= 0.5 * np.mean(negative, axis=0)

    norm = np.linalg.norm(preference)
    if norm > 0:
        preference /= norm

    return preference


def get_recommendations(conn, user_id, limit=10, offset=0, exploration_ratio=0.15):
    preference = build_preference_vector(conn, user_id)

    if preference is None:
        print("Rate some articles first.")
        return []

    candidates = conn.execute("""
                              SELECT a.id, a.title, a.source, a.category, a.url, a.embedding, a.published_at
                              FROM articles a
                                       LEFT JOIN article_ratings r ON a.id = r.article_id AND r.user_id = ?
                                       LEFT JOIN article_reads ar ON a.id = ar.article_id AND r.user_id = ?
                              WHERE r.id IS NULL
                                AND a.embedding IS NOT NULL
                                AND ar.read_at IS NULL
                              ORDER BY a.published_at DESC
                              """, (user_id, user_id)).fetchall()

    if not candidates:
        return []

    scored = []
    for article_id, title, source, category, url, blob, published_at in candidates:
        embedding = load_embedding(blob)
        score = cosine_similarity(preference, embedding)
        scored.append((score, article_id, title, source, category, url, published_at))

    # Exploitation — top articles the model is confident you'll like
    exploit_n = int(limit * (1 - exploration_ratio))

    paginated = scored[offset:]

    # Exploration — random picks from the rest to fight the filter bubble
    exploit = paginated[:exploit_n]
    explore_pool = paginated[exploit_n:]
    explore = random.sample(explore_pool, min(limit - exploit_n, len(explore_pool)))

    return exploit + explore
