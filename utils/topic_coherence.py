from sklearn.feature_extraction.text import CountVectorizer as cv
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from stop_words import get_stop_words
from utils import extract_text
from utils import topic_multibert as tm
from gensim import corpora
from gensim.models.coherencemodel import CoherenceModel
from scipy import stats


def _bow_to_gensim_corpus(bows,dictionary):
	'''create a gensim corpus.
	each line contains tuples with (word id, count)

	bows 		matrix where columns correspond to word_id and numbers to count
				rows are the texts / documents
	dictionary 	gensim dictionary keys are word ids, values are words
	'''
		
	corpus= []
	for bow in bows:
		line = []
		for i in range(len(bow)):
			count = bow[i]
			if count > 0: line.append((i,count))
		corpus.append(line)
	return corpus
	

def make_corpus_and_dictionary(texts):
	''' create gensim corpus and dictionary and a list of strings (texts).
	gensim has a function to compute topic coherence
	'''
	if type(texts[0]) != str: str_texts = [t.text for t in texts]
	else: str_texts = texts
	dutch = get_stop_words('dutch')
	count = cv(ngram_range=(1,1), stop_words=dutch).fit(str_texts)
	words = count.get_feature_names()
	dictionary = corpora.Dictionary([words])
	bows = count.transform(str_texts).toarray()
	corpus = _bow_to_gensim_corpus(bows,dictionary)
	return corpus, dictionary, str_texts
	

def compute_coherence_for_grouped_question_texts(step_size=1,steps=50):
	ad=extract_text.get_grouped_question_texts()
	md=extract_text.get_grouped_question_texts(transcriber='manual transcription')
	results = {'wl':{},'cm':{},'df':{},'n-topic':{}}
	best_results = {'wl':{},'cm':{},'df':{},'n-topic':{},'i':{}}
	for key in ad.keys():
		for i in range(2,steps,step_size):
			texts = ad[key]['texts']
			corpus, dictionary, _ = make_corpus_and_dictionary(texts)
			results,best_results = _handle_step(i,texts,key,'automatic',corpus,
				dictionary,results,best_results)
			texts = md[key]['texts']
			corpus, dictionary, _ = make_corpus_and_dictionary(texts)
			results,best_results = _handle_step(i,texts,key,'manual',corpus,
				dictionary,results,best_results)
	return results,best_results
		
def _handle_step(i,texts,key,transcription,corpus,dictionary,results,best_results):
	name = transcription + '-' + key
	step_name = str(i) + '_' + name
	print(step_name,name)
	ts,tnw,tfidf,count,df,tpt,texts = tm.make(texts,
		min_cluster_size=i,name=name)
	n_topic = len(ts) -1
	results['df'][step_name]= df
	wl = tm.topnwords_to_wordlists(tnw,ts,start=1,n_words=10)
	print('n topics found:',n_topic,key,transcription)
	results['n-topic'] = n_topic 
	results['wl'][step_name]=wl 
	cm = CoherenceModel(topics=wl,corpus=corpus,dictionary=dictionary,
		coherence='u_mass').get_coherence()
	results['cm'][step_name] = cm
	print(step_name,cm)
	if name not in best_results['cm'].keys() or cm > best_results['cm'][name]:
		if n_topic > 1: 
			for n,v in zip(['df','n-topic','wl','cm','i'],[df,n_topic,wl,cm,i]):
				best_results[n][name] = v
	return results, best_results


class Text_group:
	def __init__(self, texts, name, n_words_top = 2200, nsteps = 50,nwords= 100):
		self.texts = texts
		self.name = name
		self.n_words_top = n_words_top
		self.nsteps = nsteps
		self.nwords = nwords
		self.corpus, self.dictionary, _ = make_corpus_and_dictionary(texts)
		self.results = []
		self.make_all()

	def __repr__(self):
		m = 'text group: ' + self.name + ' | nexts: ' + str(len(self.texts))
		m += ' | nwords: ' + str(self.nwords)
		return m

	def __str__(self):
		m = self.__repr__() + '\n'
		if hasattr(self,'result'):
			m += 'MATCHED WITH: ' +self.other.__repr__() + '\n'
			m += 'OTHER RESULT: ' + self.other_result.__repr__() + '\n'
			m += self.result.__str__()
		return m

	def make_all(self):
		for i in range(2,self.nsteps):
			self.make(i)

	def make(self, min_cluster_size = 15):
		if hasattr(self,'cs_' +str(min_cluster_size)):
			return getattr(self,'cs_'+str(min_cluster_size))
		r = tm.make(self.texts,min_cluster_size=min_cluster_size, 
			n_words_top= self.n_words_top, name=self.name)[:-1]
		result = Result(*r,corpus=self.corpus,dictionary=self.dictionary,
			cluster_size = min_cluster_size, name = self.name,text_group=self,
			nwords = self.nwords)
		setattr(self,'cs_'+str(min_cluster_size),result)
		self.results.append(result)
		return result

	def get_best_result_n_or_more_topics(self,n_topics = 2):
		attrs= [n for n in dir(self) if 'cs_' in n]
		results = [getattr(self,attr) for attr in attrs]
		return max([r for r in results if r.n_topics >= n_topics ])

	def match(self,other, n_topics = 2, nwords = None, subtract = 0):
		if nwords: self.nwords = nwords
		self.other = other
		self.result = self.get_best_result_n_or_more_topics(n_topics)
		cluster_size = self.result.cluster_size
		other.result = getattr(other,'cs_' + str(cluster_size - subtract))
		self.other_result = other.result
		self.result.match_topics(other.result, nwords = nwords)
		if other.result.n_topics == 1 and cluster_size - subtract > 2: 
			# if the other result only has one topic find an result from
			# other with more topics (ie. search a result with a lower cluster size
			subtract += 1
			self.match(other, n_topics, nwords, subtract = subtract)

	

class Result:
	def __init__(self,topic_sizes,top_n_words,tf_idf,count,d,tpt,
		corpus,dictionary,cluster_size, name, text_group, nwords = 100):
		self.topic_sizes = topic_sizes
		self.top_n_words = top_n_words
		self.tf_idf = tf_idf
		self.count = count
		self.d = d
		self.texts_per_topic = tpt
		self.cluster_size = cluster_size
		self.name = name
		self.text_group = text_group
		self.nwords = nwords
		self.word_lists = tm.topnwords_to_wordlists(top_n_words,topic_sizes,
			start = 1, n_words = 10)
		self.n_topics = len(topic_sizes) -1
		self.cm = CoherenceModel(topics=self.word_lists,corpus=corpus,
			dictionary=dictionary, coherence='u_mass').get_coherence()
		self._set_topics()

	def __repr__(self):
		m = self.name+' | cs: '+str(self.cluster_size)
		m +=' | topics: '+str(self.n_topics)
		m += ' | cm: ' + str(self.cm)
		return m

	def __str__(self):
		m = self.__repr__() + '\n\n'
		m += '\n'.join([t.__repr__() for t in self.matched_topics]) +'\n'
		m += 'matched: ' + str(len(self.matched_topics))
		m += ' out of: ' + str(len(self.topics)) + ' topics'
		return m

	def __gt__(self,other):
		return self.cm > other.cm

	def _set_topics(self):
		self.topics = {}
		for key in self.top_n_words:
			if key == -1: continue
			topic = Topic(self.top_n_words,key,self, self.nwords)
			self.topics[key] = topic

	def match_topics(self,other, nwords = None):
		if nwords: self.nwords = nwords
		for key, topic in self.topics.items():
			if key == -1: continue
			topic.match(other, self.nwords)

	@property
	def matched_topics(self):
		if not hasattr(self.topics[0],'correlation'): return []
		topics = sorted(self.topics.values(), reverse = True)
		topics = [t for t in topics if t.significant]
		return topics
		

class Topic:
	def __init__(self,top_n_words, key, result,  nwords = 100):
		self.top_n_words = top_n_words
		self._set_key(key)
		self.topic_label = key
		self.result = result
		self.nwords = nwords

	def __gt__(self,other):
		return self.correlation > other.correlation

	def __repr__(self):
		m = 'key: '+str(self.key) + ' | '
		if hasattr(self,'other_key'): 
			m += 'other key: '+str(self.other_key) + ' | '
		m += 'words: ' + ' '.join([x[0] for x in self.words[:5]]) + ' | '
		if hasattr(self,'other_words'): 
			m += 'other words: '+' '.join(self.other_words.split(' ')[:5])+' | '
		if self.correlation: 
			m += 'correlation: '+str(round(self.correlation,2))+ ' | '
			m += 'p: '+str(round(self.pvalue,2))+ '\n'
		return m

	def __str__(self):
		m = self.__repr__() + '\n'
		if self.top_words: m += 'top words: '+self.top_words + '\n'
		if self.other_words: m += 'other words: '+self.other_words+ '\n'
		if self.rank_list1: m += 'ranks: '+self.rank_list1+ '\n'
		if self.rank_list2: m += 'other ranks: '+self.rank_list2+ '\n'
		return m
		

	def match(self,result, nwords = None):
		if nwords: self.nwords = nwords
		o,bo = match_top_n_words_to_dict_top_n_words(self.words,
			result.top_n_words, self.nwords)
		r,rank_list1,rank_list2,words,ow,key = bo
		result.topics[key]._set_key(key)
		self.other_key = key
		self.matched_topic = result.topics[key]
		self._set_values(words,ow,r,rank_list1,rank_list2)
		result.topics[key]._set_values(ow,words,r,rank_list2,rank_list1)

	def _set_values(self,words,ow,r, rank_list1,rank_list2):
		self.top_words = words
		self.other_words = ow
		self.r = r
		self.correlation = r.correlation
		self.pvalue = r.pvalue
		self.significant = self.pvalue < 0.5 and self.correlation >= .7
		self.rank_list1= rank_list1
		self.rank_list2= rank_list2

	def _set_key(self,key):
		self.key = key
		self.words = self.top_n_words[key]
		self.ranked_words_dict = top_n_words_to_ranked_word_dict(self.words)

		
		

def compare_top_n_words(tnw1,tnw2, nwords = 30):
	d1= top_n_words_to_ranked_word_dict(tnw1)
	d2= top_n_words_to_ranked_word_dict(tnw2)
	inv_d1 = {v: k for k, v in d1.items()}
	inv_d2 = {v: k for k, v in d2.items()}
	rank_list1, rank_list2, words,other_words = [], [], [],[]
	if nwords > len(inv_d1.keys()): nwords = len(inv_d1.keys())
	for i in range(nwords):
		rank1 = i + 1
		word = inv_d1[rank1]
		try:rank2 = d2[word]
		except:rank2 = 2200
		rank_list1.append(rank1)
		rank_list2.append(rank2)
		words.append(word)
		other_words.append(inv_d2[rank1])
	r = stats.spearmanr(rank_list1,rank_list2)
	rank_list1 = ' '.join(map(str,rank_list1[:30]))
	rank_list2 = ' '.join(map(str,rank_list2[:30]))
	return r, rank_list1, rank_list2, ' '.join(words[:10]),' '.join(other_words[:10])

def match_top_n_words_to_dict_top_n_words(tnw1,tnw_dict,nwords=10,
	skip_first=True):
	output, best_output = [], []
	best_r = -1
	for key in tnw_dict.keys():
		if skip_first == True and key == -1: continue
		tnw2 = tnw_dict[key]
		r,rank_list1,rank_list2,words,ow=compare_top_n_words(tnw1,tnw2,nwords)
		if r.correlation > best_r: 
			best_r = r.correlation
			best_output = [r,rank_list1,rank_list2,words,ow,key]
		output.append([r,rank_list1,rank_list2,words,ow])
	return output, best_output

def compare_top_n_word_dicts(tnwd1,tnwd2, nwords = 20,skip_first = True):
	best_outputs = []
	for i,tnw1 in enumerate(tnwd1.values()):
		if skip_first == True and i == 0: continue
		output,best_output=match_top_n_words_to_dict_top_n_words(tnw1,tnwd2,nwords,
			skip_first=skip_first)
		best_outputs.append(best_output)
	return best_outputs

		
def top_n_words_to_ranked_word_dict(top_n_words):
	d = {}
	for i,line in enumerate(top_n_words):
		word = line[0]
		d[word] = i+1
	return d
		
	
def match_topics_grouped_question_automatic_manual(nwords=20): 
	ad = extract_text.get_grouped_question_texts()
	md = extract_text.get_grouped_question_texts(transcriber='manual transcription')
	o = {}
	for key in ad.keys():
		print(key)
		automatic_texts= [text for text in ad[key]['texts'] if text.text]
		manual_texts = [text for text in md[key]['texts'] if text.text]
		atg = Text_group(automatic_texts,name='automatic-'+key,nwords=nwords)
		mtg = Text_group(manual_texts,name='manual-'+key,nwords=nwords)
		mtg.match(atg,nwords = nwords)
		print(mtg)
		o[key] = mtg
	return o

#compute percentage overlap of the clustering of texts

def _make_key_map(result):
	d = {-1:-1}
	for key in result.topics.keys():
		d[key] = result.topics[key].other_key
	return d

def _make_response_map(result):
	d = {}
	for i, response_pk in enumerate(result.d.response_pk):
		d[response_pk] = result.d.topic[i]
	return d

def _manual_text_group_to_perc_overlap_clustered_texts(mtg):
	key_map = _make_key_map(mtg.result)
	manual_response_to_topic_dict = _make_response_map(mtg.result)
	for key,value in manual_response_to_topic_dict.items():
		manual_response_to_topic_dict[key] = key_map[value]
	automatic_response_to_topic_dict = _make_response_map(mtg.other_result)
	correct, incorrect = 0,0
	misses = []
	for key, manual_topic in  manual_response_to_topic_dict.items():
		if key not in automatic_response_to_topic_dict.keys():
			misses.append(key)
			continue
		automatic_topic = automatic_response_to_topic_dict[key]
		if automatic_topic == manual_topic: correct += 1
		else: incorrect +=1
	perc_correct = round(correct / (correct + incorrect) * 100, 2)
	return perc_correct, correct, incorrect, misses

