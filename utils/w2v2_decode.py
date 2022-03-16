import torch
from transformers import Wav2Vec2ForCTC
from transformers import Wav2Vec2Processor
from transformers import Wav2Vec2ProcessorWithLM
from utils.w2v2_nl_lm import response2audio

from jiwer import wer
import os
import pickle
import random

from utils import w2v2_nl_lm as wnl
from texts.models import Response, Transcriber, Text

path = '../wav2vec2_cache/'

class Decoder:
	def __init__(self, recognizer_dir = '', use_cuda = False, use_lm = True, 
		word_list=None):
		if not recognizer_dir: recognizer_dir = path
		if not recognizer_dir.endswith('/'): recognizer_dir += '/'
		self.use_lm = use_lm
		self.word_list = word_list
		self.recognizer_dir = recognizer_dir
		self.logits_dir = recognizer_dir +'logits/'
		self.use_cuda = use_cuda
		self.load()
		
	def set_word_list(self,word_list):
		self.word_list = word_list

	def load(self):
		if self.use_lm: self.processor = wnl.load_processor_with_lm()
		else:self.processor = wnl.load_processor()
		self.model = wnl.load_model()
		if self.use_cuda:
			self.model = self.model.to("cuda")

	def _audio2inputs(self, audio):
		return load_inputs(audio,self.processor)

	def _inputs2logits(self,inputs):
		return inputs2logits(inputs, self.model, self.use_cuda)
	
	def _logits2labels(self,logits):
		return logits2labels(logits)

	def lm_logits2text(self,logits):
		if 'cuda' in logits.__repr__(): logits = logits.cpu()
		if self.word_list:
			return self.processor.batch_decode(logits.detach().numpy(),
				hotwords = self.word_list,
				num_processes=1).text
		return self.processor.batch_decode(logits.detach().numpy(),
			num_processes=1).text

	def audio2logits(self,audio, filename = ''):
		inputs = self._audio2inputs(audio)
		logits = self._inputs2logits(inputs)
		if filename:
			if not os.path.isdir(self.logits_dir): os.mkdir(self.logits_dir)
			with open(self.logits_dir + filename, 'wb') as fout:
				pickle.dump(logits, fout)
		return logits

	def audio2text(self,audio):
		logits = self.audio2logits(audio)
		if self.use_lm: self.lm_logits2text(logits)
		labels = self._logits2labels(logits)
		return self.processor.decode(labels)


def load_inputs(audio,processor):
	return processor(audio,return_tensors='pt',sampling_rate=16_000)

def inputs2logits(inputs, model, cuda = True):
	if cuda:
		return model(inputs.input_values.to('cuda')).logits
	return model(inputs.input_values).logits

def logits2labels(logits):
	return torch.argmax(logits, dim=-1)[0]


def get_responses():
	responses = Response.objects.exclude(audio_filename='')
	responses =responses.exclude(question__number=8)
	return responses
		
def decode_responses(decoder, use_lm = True):
	responses = get_responses()
	nresponses = responses.count()
	if use_lm: transcriber = Transcriber.objects.get(name="wav2vec2 fremy lm")
	else: transcriber = Transcriber.objects.get(name="wav2vec2 fremy")
	print('saving with transcriber name:',transcriber.name)
	for i,response in enumerate(responses):
		if not overwrite and transcriber.name in response.transcribers:
			print('already decoded:',response,'skipping',i,nresponses)
			continue
		print('decodeding:',response,i,nresponses)
		audio = response2audio(response)
		if use_lm: str_text = decoder.audio2text(audio)[0]
		else: str_text = decoder.audio2text(audio)
		text = Text(text=str_text,response = response, transcriber = transcriber)
		text.save()

def computer_wer():
	responses = get_responses()
	wav2vec2 = Transcriber.objects.get(name='wav2vec2 fremy lm')
	manual = Transcriber.objects.get(name='manual transcription')
	pred,gt,error,empty = [], [],[],[]
	for response in responses:
		try:
			x = response.text_set.get(transcriber = manual).text 
			y = response.text_set.get(transcriber = wav2vec2).text 
			if x and y:
				gt.append(x) 
				pred.append(y)
			else:empty.append(response)
		except:error.append(response)
	word_error_rate = wer(gt,pred)
	print('WER:',word_error_rate)
	return gt, pred, word_error_rate, error, empty
	
	
	
		

		
		






