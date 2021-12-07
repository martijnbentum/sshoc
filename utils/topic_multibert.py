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
from stop_words import get_stop_words
import pandas as pd
import time


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
	from utils import extract_text
	if texts == None: texts = extract_text.get_all_speech_and_keyboard_text()
	text_strs = [t.text for t in texts if t and t.text]
	model = load_model()
	embeddings = embed_sentences(text_strs, model)
	return embeddings, texts

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

def texts_to_dataframe(texts):
	'''creates a pandas dataframe from the list of text objects.
	this dataframe is needed to create texts grouped on clusters
	for the tf_idf calculation.
	'''
	d = pd.DataFrame([t.text for t in texts],columns=['text'])
	d['pk'] = [t.pk for t in texts]
	d['input_type'] = [t.input_type.name for t in texts]
	d['q'] = [t.response.question.number for t in texts]
	d['question'] = [t.response.question.title for t in texts]
	return d

def _make_defaults(save=False):
	'''this function make all default files to speed up computation
	for the 'all' case, using all usable texts.
	set save to true to overwrite existing files.
	'''
	embeddings, texts = texts_to_embeddings()
	ue = reduce_dimension_embeddings_umap(embeddings)
	d = texts_to_dataframe(texts)
	if save:
		with open('text_embeddings','wb') as fout:
			pickle.dump(embeddings,fout)
		with open('text_embeddings_umap','wb') as fout:
			pickle.dump(ue,fout)
		d.to_pickle('text_embeddings_dataframe.pkl')
	return embeddings,texts,ue,d

def make_clustered_texts(texts = None, n_dimensions = 5, min_cluster_size= 45):
	from utils import extract_text
	start = time.time()
	if texts == None: 
		texts = extract_text.get_all_speech_and_keyboard_text()
		umap_embeddings = load_text_embeddings_umap()
		d = pd.read_pickle('text_embeddings_dataframe.pkl')
	else:
		embeddings, texts = text_embeddings(texts)
		umap_embeddings=reduce_dimension_embeddings_umap(
			n_dimensions =n_dimensions)
		d = texts_to_dataframe(texts)
	clustered_embeddings=cluster(umap_embeddings,
		min_cluster_size= min_cluster_size)
	d['topic'] = clustered_embeddings.labels_
	temp = d.groupby(['topic'], as_index = False)
	texts_per_topic = temp.agg({'text': ' '.join})
	return texts_per_topic, d, texts

def tfidf(clustered_texts, ntexts):
	'''compute tfidf over clustered texts.'''
	#create an object that can convert texts into bag of words
	dutch = get_stop_words('dutch')
	count = cv(ngram_range=(1,1), stop_words=dutch).fit(clustered_texts)
	#create a matrix, rows = clustered texts, columns word counts"
	t = count.transform(clustered_texts).toarray()
	#create nwords per clustered_text
	w = t.sum(axis=1)
	#word counts per clustered text divided by nwords per document
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


def extract_top_n_words_per_topic(tf_idf, count, texts_per_topic, n = 20):
	'''extract the top n words that are most strongly associated with a topic.
	'''
	words = count.get_feature_names()
	labels = list(texts_per_topic.topic)
	#tfidf is an matrix with words as rows and topics (clustered texts) as
	#columns, by transposing the topics are on the rows
	tf_idf_transposed = tf_idf.T
	#get n indices of the words strongly associated with a topic
	#the argsort returns the indices that would sort the array
	indices = tf_idf_transposed.argsort()[:,-n:]
	top_n_words = {}
	#create a dictionary that maps a topic label to top n words with tf_idf score
	for i, label in enumerate(labels):
		top_n_words[label] = []
		for index in indices[i][::-1]:
			top_n_words[label].append([words[index],tf_idf_transposed[i][index]])
	return top_n_words

def extract_topic_sizes(dataframe):
	topic_sizes = (dataframe.groupby(['topic'])
		.text
		.count()
		.reset_index()
		.rename({'topic':'topic','text':'size'},axis='columns')
		.sort_values('size',ascending=False))
	return topic_sizes

def make():
	tpt,d, texts = tm.make_clustered_texts(min_cluster_size=15)

def topnwords_to_wordlists(top_n_words,topic_sizes, n = 10):
	wordlists = []
	for topic in topic_sizes.topic[1:n+1]:
		wordlists.append(' '.join([x[0] for x in top_n_words[topic][:n]]))
	return wordlists


