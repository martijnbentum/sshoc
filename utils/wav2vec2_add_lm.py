# https://huggingface.co/blog/wav2vec2-with-ngram
# based on the above tutorial, wav2vec2 with ngram decoding
# transformer based decoding can give a futher improvement
# based on frisian /vol/tensusers/mbentum/FRISIAN_ASR/repo/utils/wav2vec2_lm.py

from pyctcdecode import build_ctcdecoder
from transformers import Wav2Vec2Processor
from transformers import Wav2Vec2ProcessorWithLM
from transformers import Wav2Vec2ForCTC
import torch

import os

path = '../wav2vec2_cache/'
lm_filename = '/vol/tensusers4/ctejedor/MJ/LM/custom.lm'

'''
the path directory should contain the following:
config.json 						(unknown)
preprocessor_config.json 			(load the tokenizer /processor)
pytorch_model.bin 					(model weights)
vocab.json 							(needed to load processor)
-----------
'''

def load_pretrained_processor(recognizer_dir = ''):
	if not recognizer_dir: 
		print('no directory provided, using default at:',path)
		recognizer_dir = path
	processor = Wav2Vec2Processor.from_pretrained(recognizer_dir)
	return processor

def load_and_sort_vocab(processor = None, recognizer_dir = path):
	if not processor:
		print('no processor provided, using default at:',recognizer_dir)
		processor = load_pretrained_processor(recognizer_dir)
	vocab = processor.tokenizer.get_vocab()
	sorted_vocab = sorted(vocab.items(), key = lambda item: item[1])
	sorted_vocab = {k.lower():v for k, v in sorted_vocab}
	return sorted_vocab

def make_ctc_decoder(sorted_vocab = None, lm_filename = lm_filename):
	if not sorted_vocab:
		print('no vocab provided, using default based on processor form:',path)
		processor = load_pretrained_processor(path)
		sorted_vocab = load_and_sort_vocab(processor)
	labels = list(sorted_vocab.keys())
	decoder = build_ctcdecoder(labels=labels,kenlm_model_path=lm_filename)
	return decoder
		
def make_processor_with_lm(input_recognizer_dir='', save = True, 
	output_recognizer_dir = '', lm_filename = lm_filename):
	if not input_recognizer_dir: 
		print('no directory provided, using default at:',path)
		input_recognizer_dir= path
	if save and output_recognizer_dir:
		if os.path.isdir(output_recognizer_dir):
			raise ValueError('output dir:', output_recognizer_dir,'already exists') 
		os.system('cp -r ' + input_recognizer_dir + ' ' + output_recognizer_dir)
	else: 
		m = 'set save to true and provide an output_recognizer_dir' 
		m += 'to save processor\nsave:' + str(save) + ' output_recognizer_dir:'
		m += str(output_recognizer_dir)
		raise ValueError(m)
	processor = load_pretrained_processor(output_recognizer_dir)
	sorted_vocab = load_and_sort_vocab(processor)
	decoder = make_ctc_decoder(sorted_vocab, lm_filename)
	processor_with_lm = Wav2Vec2ProcessorWithLM(
		feature_extractor = processor.feature_extractor,
		tokenizer = processor.tokenizer,
		decoder = decoder
	)
	if save and output_recognizer_dir:
		processor_with_lm.save_pretrained(output_recognizer_dir)
	return processor_with_lm

def load_processor_with_lm(recognizer_dir = ''):
	if not recognizer_dir: recognizer_dir = path
	return Wav2Vec2ProcessorWithLM.from_pretrained(recognizer_dir)
	

def load_model(recognizer_dir = ''):
	if not recognizer_dir: recognizer_dir = path
	# should .to('cuda') be added below?
	model = Wav2Vec2ForCTC.from_pretrained(recognizer_dir)
	return model
