from transformers import Wav2Vec2Processor
from transformers import Wav2Vec2ProcessorWithLM
from transformers import Wav2Vec2ForCTC

import glob
import librosa
import os
# from texts.models import Response
# from utils import w2v2_decode as wd

cache_dir = '../wav2vec2_cache/'
recognizer_dir = '../wav2vec2_cache/'
wav_dir = '../../wav_16k/'
wav_fn = glob.glob('*.wav')

def load_processor_with_lm(recognizer_dir):
	processor = Wav2Vec2ProcessorWithLM.from_pretrained(recognizer_dir)
	'''
	processor = Wav2Vec2ProcessorWithLM.from_pretrained(
		'FremyCompany/xls-r-2b-nl-v2_lm-5gram-os',
		cache_dir = cache_dir
	)
	'''
	return processor

def load_processor(recognizer_dir):
	processor = Wav2Vec2Processor.from_pretrained(recognizer_dir)
	'''
	processor = Wav2Vec2Processor.from_pretrained(
		'FremyCompany/xls-r-2b-nl-v2_lm-5gram-os',
		cache_dir = cache_dir
	)
	'''
	return processor

def load_model(recognizer_dir):
	processor = load_processor(recognizer_dir)
	model = Wav2Vec2ForCTC.from_pretrained(recognizer_dir)
	'''
	model = Wav2Vec2ForCTC.from_pretrained(
		'FremyCompany/xls-r-2b-nl-v2_lm-5gram-os',
		cache_dir = cache_dir
	)
	# model.freeze_feature_extractor() not sure if needed if not finetuning
	'''
	return model

'''
def load_decoder():
	return wd.Decode(recognizer_dir,use_lm=True)
'''

def load_audio(filename, sample_rate=None):
	np_array, sample_rate = librosa.load(filename,sr=sample_rate)
	return np_array, sample_rate


def response2audio(response):
	if not response.audio_filename:return 'no audiofilename'
	audio_filename = response.audio_filename
	if not audio_filename.endswith('.wav'): audio_filename += '.wav'
	path = wav_dir + audio_filename
	if not os.path.isfile(path): return 'file not found'
	np_array, sample_rate = load_audio(path)
	assert sample_rate == 16000
	return np_array
