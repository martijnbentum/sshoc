import glob
from utils.split_audio import load_audio, splice_audio
from utils.w2v2_decode import Decoder
from jiwer import wer
import os

directory = '/vol/tensusers4/ctejedor/MJ/'
audio_directory = directory + 'audio/'
lexicon_directory = directory + 'lexicons/'
audio_files = glob.glob(audio_directory + '*.wav')
output_dir = '../homed/'

def load_text():
	return [x for x in open(directory + 'text.txt').read().split('\n') if x]

def load_terms():
	words  =  open(lexicon_directory+ 'terms.lex').read().split('\n') 
	return [word for word in words  if word]

def load_custom():
	words  =  open(lexicon_directory+ 'custom.lex').read().split('\n') 
	return [word for word in words  if word]

def directory_is_empty(directory):
	if not directory.endswith('/'): directory += '/'
	return len(glob.glob(directory + '*')) == 0
	
def save_transcription(name,transcription):
	with open( name, 'w') as fout:
		fout.write(transcription)
	print('saved:',name)
	print('transcription:',transcription)

def check_chunk_length():
	return

def decode_audio(decoder,output_directory = None, overwrite = False, 
	audio_filenames = None):
	if not audio_filenames: audio_filenames = audio_files
	if not output_directory: output_directory = output_dir
	if not output_directory.endswith('/'): output_directory += '/'
	print('saving decoding output to:',output_directory)
	for i,filename in enumerate(audio_filenames):
		print(i,filename,len(audio_filenames))
		name = output_directory+filename.split('/')[-1].replace('.wav','.txt')
		if os.path.isfile(name):
			print(name, 'already exists, set overwrite =True to overwrite it')
			continue
		audio_chunks= splice_audio(filename)
		texts = []
		for st,et in audio_chunks:
			print('duration:',(et-st)/16000)
			audio, sr = load_audio(filename, 16000)
			audio = audio[st:et]
			text = decoder.audio2text(audio)[0]
			texts.append(text)
			if text:
				print('transcription:',text[:60],'[...]')
		save_transcription(name,'\n'.join(texts))

def get_ground_truth_and_predictions(output_directory = None):
	if not output_directory: output_directory = output_dir
	if not output_directory.endswith('/'): output_directory += '/'
	text = load_text()
	pred_filenames = glob.glob(output_directory + '*.txt')
	gt,pred, names = [], [], []
	for line in text:
		gt_transcription, name = line.split(' (')
		name = name.split('-')[0]
		for pred_filename in pred_filenames:
			pred_name = pred_filename.split('/')[-1].split('.')[0]
			if  pred_name == name:
				pred_transcription=open(pred_filename).read().replace('\n',' ') 
				names.append([name,pred_filename])
				gt.append(gt_transcription)
				pred.append(pred_transcription)
	return gt, pred, names


def compute_wer(output_directory = None):
	gt, pred,names = get_ground_truth_and_predictions(output_directory)
	word_error_rate = wer(gt,pred)
	return word_error_rate, gt,pred,names
