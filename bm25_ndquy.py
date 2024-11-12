from utils import *
from bm25_ndquy_implement import BM25

path_to_corpus = 'demo-wiki'

def get_docs(docs_dir):
    docs = []
#     f_w = open('./datatrain.txt', 'w')
    for i, sub_dir in enumerate(os.listdir(path_to_corpus)):
        path_to_subdir = path_to_corpus + '/' + sub_dir
        print(path_to_subdir)
        if os.path.isdir(path_to_subdir):
            for j, file_name in enumerate(os.listdir(path_to_subdir)):
                print(file_name)
                with open(path_to_subdir + '/' + file_name) as f_r:
                    contents = f_r.read().strip().split('</doc>')
                    for content in contents:
                        if (len(content) < 5):
                            continue
                        content = clean_text(content)
                        content = word_segment(content)
                        content = remove_stopword(normalize_text(content))
                        docs.append(content)
    return docs

docs = get_docs(path_to_corpus)

texts = [
    [word for word in document.lower().split() if word not in list_stopwords]
    for document in docs
]

bm25 = BM25()
bm25.fit(texts)
