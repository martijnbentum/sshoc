from blessed import Terminal
import glob
import os
import random

RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
BOLD = '\033[1m' 
UNDERLINE = '\033[4m'
ENDC = '\033[0m'

sentiment_filename = 'sentiment_responses.txt'
key_dict = {'s':'negative','g':'positive','n':'neutral','t':'back','q':'quit'}

def make_filename(name):
	'''makes a filename for a specific rater.'''
	return sentiment_filename.split('.')[0] + '_' + name + '.txt'

def print_continue_instruction(allowed):
	print("Druk op ",', '.join(allowed),' om door te gaan')

def instructions():
	m = '\n\n\nHet is de bedoeling dat je antwoorden op sentiment beoordeelt\n'
	m += 'Je kan hiervoor de volgende knoppen gebruiken:\n\n'
	m += 's (slecht) voor negatief sentiment\n'
	m += 'g (goed) voor positief sentiment\n'
	m += 'n (neutraal) voor neutraal sentiment, of niet beoordeelbaar op sentiment\n\n'
	m += 'Als je een vorig antwoord wilt beoordelen druk dan op: t\n'
	m += 'Als je wilt stoppen druk op: q\n\n'
	m += 'Je beoordelingen worden automatisch opgeslagen en je kan '
	m += 'de volgende keer verder gaan waar je gebleven was.\n\n\n'
	return m

def get_input(prompt = '',allowed=['s','g','n','t','q']):
	'''get response from rater'''
	term = Terminal()
	with term.cbreak(): # set keys to be read immediately 
		if prompt:print(prompt)
		else:print_continue_instruction(allowed)
		inp = term.inkey() # wait and read one character
		if allowed == None or inp in allowed:
			return inp
		print('gebruik:',' '.join(allowed))
		return get_input(allowed)

def get_name():
	name = input('\n\n\nVoer je naam in en druk op enter: ')
	responses, filename = load_responses(name)
	if filename == sentiment_filename:
		m = 'Nog geen bestand gevonden met beoordelingen voor: ' + name
		m += '\nWil je een nieuw bestand maken? j/n'
		inp = get_input(prompt= m, allowed =['j','n'])
		if inp == 'n': return get_name()
		return responses, make_filename(name)
	else: return responses, filename

def get_next_response_index(responses,index,overwrite):
	'''selects the next response to be rated.'''
	if index == len(responses): return None
	response = response_line_to_dict(responses[index])
	if not overwrite: 
		if response['rating']: 
			return get_next_response_index(responses,index+1,overwrite)
		else: return index
	if overwrite: return index
		
def rate_response(responses,index, filename):
	clear_screen()
	response = response_line_to_dict(responses[index])
	m = BLUE + instructions() + ENDC + '\n\n\n'
	m += GREEN+ 'Vraag: ' + response['question'] +'\n\n\n' + ENDC
	m += 'Antwoord:' + response['answer'] +'\n\n\n'
	inp = get_input(prompt=m)
	rating = key_dict[inp]
	if rating == 'back': return 'back'
	if rating == 'quit': return 'quit'
	response['rating'] = rating
	responses[index] = response_dict_to_line(response)
	save_file(responses,filename)
	return 'forward'

def rate_responses(responses,filename):
	nresponses = len(responses)
	random.shuffle(responses)
	index = 0
	overwrite = False
	while True:
		index = get_next_response_index(responses,index,overwrite)		
		if index == None:
			print('Alle antwoorden zijn beoordeeld')
			break
		x = rate_response(responses,index, filename)
		if x == 'back':
			index -= 1
			overwrite = True
		elif x == 'quit':
			print('Je hebt: ',get_n_rated(responses),' antwoorden beoordeeld')
			print('van de: ',nresponses,' antwoorden')
			break
		else: index += 1

def get_n_rated(responses):
	n = 0
	for line in responses:
		d = response_line_to_dict(line)
		if d['rating']: n +=1
	return n

def clear_screen():
	os.system('clear')

def load_responses(name = None):
	'''load the sentiment_filename file to rate responses on sentiment.'''
	filename = sentiment_filename
	if name: 
		fn = glob.glob(make_filename(name))
		if len(fn) == 1: filename = fn[0]
	responses = open(filename).read().split('\n')
	return responses, filename

def response_line_to_dict(response_line):
	'''creates a dict based on a line in the sentiment_responses file.
	contains answer to be rated, question and possbile rating (if the file was rated by same rater)
	'''
	column_names = 'id,answer,question,question_number,rating'.split(',')
	l = response_line.split('\t')
	d = {}
	for i,name in enumerate(column_names):
		if i < len(l):d[name] = l[i]
		else: d[name] = ''
	return d

def response_dict_to_line(response_dict):
	'''creates a list based on a response_dict to save.'''
	return '\t'.join( list(response_dict.values()))


def save_file(responses,filename,verbose=True):
	if verbose:print('beoordelingen worden opgeslagen in:',filename)
	with open(filename,'w') as fout:
		fout.write('\n'.join(responses))
			
	
def do_rating():
	clear_screen()
	responses,filename = get_name()
	rate_responses(responses,filename)
	
	
if __name__ == "__main__":
	do_rating()
