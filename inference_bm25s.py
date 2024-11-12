from utils.preprocess import TextPreprocessor
from utils.io import read_json, save_to_json
from utils.dataset import search_by_id
from tqdm import tqdm
from bm25s.hf import BM25HF

def splitter(text, preprocessor):
    return preprocessor.preprocess(text).split()

def index_and_save(corpus, preprocessor, hub_path="Turbo-AI/corpus-index"):
    corpus_tokens = [splitter(doc, preprocessor) for doc in tqdm(corpus)]
    retriever = BM25HF()
    retriever.index(corpus_tokens)
    retriever.save_to_hub(hub_path, corpus=corpus)
    return retriever

def load_index_from_hub(hub_path="Turbo-AI/corpus-index"):
    return BM25HF.load_from_hub(hub_path, load_corpus=True, mmap=True)

def retrieve_query(corpus, query, retriever, preprocessor, top_k=3):
    query_tokens = [splitter(query['text'], preprocessor)]
    ids, scores = retriever.retrieve(query_tokens, k=top_k)
    ids, scores = ids[0], scores[0]
    max_score = max(scores)
    relevants = []
    for item in ids:
        relevants.append(corpus[item['id']]['id'])
    result = {
        'id': query['id'],
        'text': query['text'],
        'relevant': relevants,
        'scores': (scores / max_score).tolist()
    }
    return result

def eval_dev(corpus, queries, retriever, preprocessor, top_k=3):
    results_dev = []
    mrr_scores = []
    for query in tqdm(queries):
        result = retrieve_query(corpus, query, retriever, preprocessor, top_k=top_k)
        results_dev.append(result)

        true_relevants = [item['id'] for item in query['relevant']]
        mrr_score = 0
        for rank, relevant_predict in enumerate(result['relevant']):
            if relevant_predict in true_relevants:
                mrr_score += 1 / (rank + 1)
        mrr_scores.append(mrr_score / len(true_relevants))
    
    return results_dev, sum(mrr_scores) / len(mrr_scores)

def eval_test(corpus, queries, retriever, preprocessor, top_k=3):
    results = []
    for query in tqdm(queries):
        result = retrieve_query(corpus, query, retriever, preprocessor, top_k=top_k)
        results.append(result)
    
    return results

def generate(corpus, queries, retriever, preprocessor, top_k=3):
    results = []
    for query in tqdm(queries):
        result = retrieve_query(corpus, query, retriever, preprocessor, top_k=top_k)
        true_relevants = [item['id'] for item in query['relevant']]
        negatives = [doc_id for doc_id in result['relevant'] if doc_id not in true_relevants]
        query['not_relevant'] = [{'id': cid, 'text': search_by_id(data=corpus, search_id=cid)['text']} for cid in negatives]
        results.append(query)
    return results

if __name__ == "__main__":
    config = read_json('configs/bm25s_config.json')

    stopwords_file = config["stopwords_path"]
    corpus_file = config["corpus_path"]
    hub_id = config["hub_id"]
    top_k = config["top_k"]

    preprocessor = TextPreprocessor(stopwords_file=stopwords_file)

    corpus = read_json(corpus_file)

    if config["create_index"]:
        list_corpus = [item['text'] for item in corpus]
        retriever = index_and_save(list_corpus, preprocessor, hub_path=hub_id)

    retriever = load_index_from_hub(hub_path = hub_id)
    queries = read_json(config['query_path'])

    if config["is_dev"]:
        result, mrr_score = eval_dev(corpus, queries, retriever, preprocessor, top_k=top_k)
        print("MRR score: ", mrr_score)
        save_to_json(result, config['result_path'])

    if config["is_test"]:
        result = eval_test(corpus, queries, retriever, preprocessor, top_k=top_k)
        save_to_json(result, config['result_path'])

    if config["is_generate"]:
        queries = read_json(config['train_path'])
        result = generate(corpus, queries, retriever, preprocessor, top_k=3)
        save_to_json(result, config['generate_path'])