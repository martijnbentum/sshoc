'''
inspired by:
https://github.com/MaartenGr/BERTopic
https://towardsdatascience.com/topic-modeling-with-bert-779f7db187e6
maybe also relevant:
https://github.com/ddangelov/Top2Vec
'''
from django.apps import apps
from sklearn.feature_extraction.text import CountVectorizer as cv
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle


def download_model():
	f = 'sentence-transformers/distiluse-base-multilingual-cased-v2'
	model = SentenceTransformer(f)
	return model

def load_model():
	fin = open('topic_sentence_transformer_multilingual_bert','rb')
	return pickle.load(fin)

def embed_sentences(s,model = None):
	if not model: model = load_model()
	return model.encode(s,show_progress_bar = True)

def text_to_embedding(text, model = None):
	if type(text) == str: pass
	else: text = text.text
	return embed_sentences(text,model)

def texts_to_embeddings(texts = None):
	'''create sentence embeddings based on multilingual_bert'''
	if texts == None:texts= apps.get_model('texts','text').objects.all()
	texts = [t.text for t in texts if t and t.text]
	model = load_model()
	embeddings = embed_sentences(texts, model)
	return embeddings

def load_text_embeddings():
	'''load presaved sentence embeddings.'''
	fin = open('text_embeddings','rb')
	return pickle.load(fin)

def reduce_dimension_embeddings_umap(embeddings = None, n = 5):
	'''lower dimension of embeddings form 512 (bert embeddings output) to n
	'''
	if embeddings is None: embeddings = load_text_embeddings()
	import umap
	u = umap.UMAP(n_neighbors=15,n_components=n,metric='cosine')
	return u.fit_transform(embeddings)

def load_text_embeddings_umap():
	'''load presaved text embeddings with lower dimension.'''
	fin = open('text_embeddings_umap','rb')
	return pickle.load(fin)

def cluster(embeddings = None, min_cluster_size = 45):
	'''cluster embeddings. the min cluster size indicates the  number
	examples are needed for a cluster
	'''
	if embeddings is None: embeddings = load_text_embeddings_umap()
	import hdbscan
	c = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
		metric='euclidean',
		cluster_selection_method='eom')
	return c.fit(embeddings)

def tfidf(clustered_texts, ntexts):
	'''compute tfidf over clustered texts.'''
	#create an object that can convert texts into bag of words
	count = cv(ngram_range(1,1), stop_words='dutch').fit(clustered_texts)
	#create a matrix, rows = clustered texts, columns word counts"
	t = count.transform(documents).toarray()
	#create nwords per document
	w = t.sum(axis=1)
	#word counts per clustered texts divided by nwords per document
	tf = np.divide(t.T,w)
	#overall word counts (counted over all clustered texts)
	sum_t = t.sum(axis=0)
	#the number of clustered texts is divided by overall word counts
	#results in the document frequency??
	idf = np.log(np.divide(ntexts,sum_t)).reshape(-1,1)
	#multiply term frequencies with document frequencies
	#rows = words, columns = texts
	tf_idf = np.multiply(tf,idf)
	return tf_idf, count


