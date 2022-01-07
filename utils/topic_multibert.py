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
import os
from utils import extract_text

embeddings_folder = '../embeddings/'


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
	fin = open(embeddings_folder+'text_embeddings','rb')
	return pickle.load(fin)

def reduce_dimension_embeddings_umap(embeddings = None, n = 5):
	'''lower dimension of embeddings form 512 (bert embeddings output) to n
	'''
	if embeddings is None: embeddings = load_text_embeddings()
	import umap
	u = umap.UMAP(n_neighbors=15,n_components=n,metric='cosine')
	return u.fit_transform(embeddings)

def load_text_embeddings_umap(name = None):
	'''load presaved text embeddings with lower dimension.'''
	if not name: name = 'text_embeddings_umap'
	fin = open(embeddings_folder +name,'rb')
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
		with open(embeddings_folder +'text_embeddings','wb') as fout:
			pickle.dump(embeddings,fout)
		with open(embeddings_folder +'text_embeddings_umap','wb') as fout:
			pickle.dump(ue,fout)
		d.to_pickle(embeddings_folder +'text_embeddings_dataframe.pkl')
	return embeddings,texts,ue,d


def texts_to_umap_embeddings(texts, name = None, overwrite = False, n_dimensions=5):
	if texts == None: 
		texts = extract_text.get_all_speech_and_keyboard_text()
		umap_embeddings = load_text_embeddings_umap()
	else:
		if name and os.path.isfile(embeddings_folder +name) and not overwrite:
			umap_embeddings = load_text_embeddings_umap(name)
		else:
			embeddings, _ = texts_to_embeddings(texts)
			umap_embeddings=reduce_dimension_embeddings_umap(embeddings =embeddings,
				n=n_dimensions)
			if name:
				with open(embeddings_folder + name,'wb') as fout:
					pickle.dump(umap_embeddings,fout)
	return umap_embeddings, texts

def make_clustered_texts(texts = None, n_dimensions = 5, min_cluster_size= 45, 
	name = None, overwrite = False):
	start = time.time()
	if texts == None:
		d = pd.read_pickle(embeddings_folder+'text_embeddings_dataframe.pkl')
	else: d = texts_to_dataframe(texts)
	umap_embeddings, texts = texts_to_umap_embeddings(texts,name,overwrite,
		n_dimensions)
	clustered_embeddings=cluster(umap_embeddings,
		min_cluster_size= min_cluster_size)
	d['topic'] = clustered_embeddings.labels_
	temp = d.groupby(['topic'], as_index = False)
	texts_per_topic = temp.agg({'text': ' '.join})
	return texts_per_topic, d, texts

def make_tfidf(clustered_texts, ntexts):
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

def make(texts = None, min_cluster_size = 15,n_dimensions = 5,n_words_top=20,
	name=None):
	tpt,d, texts = make_clustered_texts(texts = texts,
		min_cluster_size=min_cluster_size,name =name)
	tf_idf, count = make_tfidf(tpt.text.values,len(texts))
	top_n_words = extract_top_n_words_per_topic(tf_idf, count, tpt, n = n_words_top)
	topic_sizes = extract_topic_sizes(d)
	return topic_sizes, top_n_words,tf_idf,count,d,tpt,texts

def topnwords_to_wordlists(top_n_words,topic_sizes, n_words = 10,n_topics=10,
	start = 1):
	wordlists = []
	for topic in topic_sizes.topic[1:n_topics+1]:
		wordlists.append([x[0] for x in top_n_words[topic][:n_words]])
	return wordlists

def topic_modelling_for_grouped_questions():
	from . import extract_text
	from .color import color
	import os
	d = extract_text.get_grouped_question_texts()
	output = {}
	os.system('clear')
	for key, value in d.items():
		print(color(key,'underline'))
		texts = value['texts']
		print(color('n texts: ' +str(len(texts)),'blue'))
		topic_sizes, top_n_words,tf_idf,count,d,tpt, texts = make(texts=texts)
		wordlists = topnwords_to_wordlists(top_n_words,topic_sizes)
		output[key]=[topic_sizes,top_n_words,tf_idf,count,d,tpt,texts,wordlists]
		print('\n'.join([' '.join(wl) for wl in wordlists]))
		print(color('-'*90,'blue'))
	return output




