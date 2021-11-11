'''
inspired by:
https://github.com/MaartenGr/BERTopic
https://towardsdatascience.com/topic-modeling-with-bert-779f7db187e6
maybe also relevant:
https://github.com/ddangelov/Top2Vec
'''
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
	return model.encode(s)
