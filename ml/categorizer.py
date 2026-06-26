from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CATEGORY_SEEDS = {
    "Війна та безпека": "армія зсу фронт обстріл ракета окупація бойові нато зброя дрон мобілізація",
    "Політика": "президент парламент верховна рада уряд міністр закон вибори партія депутат",
    "Економіка": "гривня бюджет інфляція ввп банк нбу економіка ринок долар євро санкції",
    "Технології": "штучний інтелект технології стартап додаток кібер програмування цифровий",
    "Спорт": "футбол матч чемпіонат команда гравець динамо шахтар олімпіада турнір",
    "Суспільство": "освіта медицина культура церква суспільство соціальний волонтер",
}


def categorize_articles(conn):
    articles = conn.execute(
        "SELECT id, title, summary FROM articles WHERE category IS NULL"
    ).fetchall()

    if not articles:
        print("Nothing to categorize.")
        return

    category_names = list(CATEGORY_SEEDS.keys())
    seed_texts = list(CATEGORY_SEEDS.values())

    # Combine title + summary — title carries strong signal
    article_texts = [f"{title} {summary or ''}" for _, title, summary in articles]

    # Fit on EVERYTHING so articles and seeds share the same vocabulary
    vectorizer = TfidfVectorizer(max_features=5000)
    all_vectors = vectorizer.fit_transform(article_texts + seed_texts)

    article_vectors = all_vectors[: len(article_texts)]
    seed_vectors = all_vectors[len(article_texts):]

    # Each row = one article, each column = similarity to one category
    similarities = cosine_similarity(article_vectors, seed_vectors)

    updates = []
    for i, (article_id, _, _) in enumerate(articles):
        best_idx = similarities[i].argmax()
        best_score = similarities[i][best_idx]
        # If similarity is too low, the article fits no category well
        category = category_names[best_idx] if best_score > 0.05 else "Інше"
        updates.append((category, article_id))

    conn.executemany("UPDATE articles SET category = ? WHERE id = ?", updates)
    conn.commit()
    print(f"Categorized {len(updates)} articles.")


def print_results(conn):
    rows = conn.execute("""
                        SELECT category, COUNT(*) as n
                        FROM articles
                        GROUP BY category
                        ORDER BY n DESC
                        """).fetchall()
    print()
    for category, count in rows:
        bar = "█" * (count // 3)
        print(f"{category:<22} {count:>4}  {bar}")
