import logging

import pandas as pd
from kmodes.kmodes import KModes
from mlxtend.frequent_patterns import association_rules
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

from .processor import corr_tfidf_to_questions, extract_value
from .processor import log_with_print

logger = logging.getLogger(__name__)


def k_mode_clusters(answers, len_questions):
    k_mode_data = [[code[:3] for code in answer] for answer in answers]
    df = pd.DataFrame(k_mode_data)
    df = df.fillna("999")
    silhouette_scores = []
    logger.info("Подбираем оптимальное число кластеров...")
    for n_clusters in range(3, round(len_questions / 5)):  # проверяем от 2 до 6
        km = KModes(n_clusters=n_clusters, init='Cao', n_init=5, verbose=0)
        clusters = km.fit_predict(df)
        try:
            score = silhouette_score(df, clusters, metric="hamming")
            silhouette_scores.append((n_clusters, score))
            logger.info(f"Silhouette Score для {n_clusters} кластеров: {score:.4f}")
        except:
            log_with_print(f"Не удалось вычислить Silhouette Score для {n_clusters} кластеров")
    best_n, best_score = max(silhouette_scores, key=lambda x: x[1])
    log_with_print(f"Лучшее число кластеров для текущей выборки: {best_n}")
    km = KModes(n_clusters=best_n, init='Huang', n_init=10)
    clusters = km.fit_predict(df)
    df["cluster"] = clusters
    return df, best_n


def get_strong_pairs(answers, ignored_codes, possible_answers_list, questions, strong_pairs_coefficient):
    vectorizer = TfidfVectorizer()
    texts = [" ".join(code[:3] for code in row if code[:3] not in ignored_codes) for row in answers]
    x = vectorizer.fit_transform(texts)
    tfidf_df = pd.DataFrame(x.toarray(), columns=vectorizer.get_feature_names_out())
    correlation_matrix = tfidf_df.corr()
    questions_corr = corr_tfidf_to_questions(correlation_matrix, possible_answers_list, questions)
    strong_pairs = questions_corr.stack().reset_index()
    strong_pairs.columns = ["Вопрос 1", "Вопрос 2", "Корреляция"]
    strong_pairs = strong_pairs[strong_pairs["Корреляция"] > strong_pairs_coefficient]
    strong_pairs_index = strong_pairs.copy()
    column_to_index = {col: idx for idx, col in enumerate(questions_corr.columns)}
    strong_pairs_index["Вопрос 1"] = strong_pairs["Вопрос 1"].map(column_to_index)
    strong_pairs_index["Вопрос 2"] = strong_pairs["Вопрос 2"].map(column_to_index)
    return strong_pairs_index


def get_rules(answers):
    te = TransactionEncoder()
    te_ary = te.fit(answers).transform(answers)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = fpgrowth(df, min_support=0.01, use_colnames=True, max_len=2)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.01)
    rules["antecedents"] = rules["antecedents"].apply(extract_value)
    rules["consequents"] = rules["consequents"].apply(extract_value)
    return rules
