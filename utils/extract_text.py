from texts.models import Variable,Session,Response,Inputtype,Person,Text,Question
from texts.models import Transcriber

def get_all_speech_and_keyboard_text(question = 'all', transcriber = 'questfox'):
	speech_text = question2text(question = question, transcriber = transcriber)
	keyboard_text = question2text(input_type='keyboard', question = question)
	texts = list(speech_text) + list(keyboard_text)
	return texts

def get_questions(condition = 'audio', exclude_q8 = True):
	return Question.objects.filter(number__gte = 9).filter(condition = condition)

def get_responses(questions = [],exclude_q8 = True):
	'''get all responses order by person.
	by default excluded question 8 because this has no content (test sentence)
	'''
	if questions == []:
		if exclude_q8:r = Response.objects.filter(question__number__gte = 9)
		else: r = Response.objects.all()
	else:
		r = Response.objects.filter(question__number__in = questions)
	r.order_by('person__number')
	return r

def _handle_question(question, exclude_q8 = True):
	'''retrieves a single question from database'''
	if hasattr(question,'number'):question = question.number
	if question == 'all': 
		if exclude_q8:question = Question.objects.filter(number__gte =9)
		else: question = Question.objects.all()
		question = [instance.number for instance in question]
	if type(question) == str:
		if ',' in question: question = question.split(',')
		else: question = int(question)
	if type(question) == int: question = [question]
	return question

def _handle_transcriber(transcriber):
	if type(transcriber) != str:
		try: transcriber = transcriber.name
		except:
			transcriber = 'questfox'
			print('transcriber should be string or transcriber instance')
			print('using questfox as transcriber')
	return transcriber

def question2text(question = 'all', transcriber = 'questfox',exclude_q8 = True,
	input_type= 'speech', only_include_ok = True):
	'''get all text instance ordered by person.
	by default excluded question 8 because this has no content (test sentence)
	'''
	print('q',question)
	question = _handle_question(question, exclude_q8)
	print('q',question)
	transcriber = _handle_transcriber(transcriber)
	t = Text.objects.filter(response__question__number__in = question)
	if only_include_ok:t = t.filter(include = True)
	if input_type == 'keyboard':t = t.filter(input_type__name= input_type)
	else:t = t.filter(transcriber__name = transcriber)
	return t.order_by('response__person__number')

	
def question2str(question='all',transcriber='questfox', exclude_q8 = True, 
	show_person = True, show_question = True, show_transcriber = False,
	show_audio_filename = False, show_audio_quality = False, 
	only_include_ok = True):
	'''creates a str output of texts based on question set.
	'''
	output = []
	texts = question2text(question,transcriber,exclude_q8,
		only_include_ok = only_include_ok)
	for text in texts:
		line = []
		line.append(text.text)
		if show_person: line.append(str(text.person))
		if show_question: line.append(str(text.question))
		if show_transcriber: line.append(str(text.transcriber))
		if show_audio_filename: line.append(str(text.audio_filename))
		if show_audio_quality: line.append(str(text.audio_quality))
		output.append('\t'.join(line))
	return '\n'.join(output)
	
def get_all_text_for_question(number, transcriber = 'questfox'):
	return question2str(number, transcriber, show_person=False,
		show_question=False)

def get_all_text_for_all_questions(transcriber = 'questfox'):
	return question2str(transcriber = transcriber, show_person=False,
		show_question=False)

def get_questions(questions = []):
	if type(questions) == int: questions = [questions]
	return Question.objects.filter(number__in = questions)
	
def group_questions(numbers=True):
	d={'democracy':[13,14,15,16,17,18]}
	d.update({'europe':[20,21,22,23,24,25]})
	d.update({'trust':[27,28,29,30,31,32]})
	d.update({'marriage':[34,35,36,41,42,43,37,38,39,44,45,46]})
	if numbers: return d
	o = {}
	for key,value in d.items():
		o[key] = get_questions(value)
	return o

def get_grouped_question_texts(input_type = 'both',transcriber= 'questfox'):
	d = group_questions()
	o = {}
	for key, value in d.items():
		o[key] = {'questions':value}
		if input_type == 'both':
			texts= get_all_speech_and_keyboard_text(question=value,
				transcriber=transcriber)
		else:
			texts=question2text(question=value,transcriber=transcriber,
				input_type = input_type)
		o[key].update({'texts':texts})
	return o
	

def sentiment_analysis_questions(numbers = True):
	q = [13,15,20,22,29,16,18,23,25,32]
	if not numbers:return get_questions(q)
	return q


def get_sentiment_text(input_type = 'both',transcriber='questfox'):
	questions = sentiment_analysis_questions()
	print(questions)
	if input_type == 'both':
		texts = get_all_speech_and_keyboard_text(question = questions, 
			transcriber = transcriber)
	else: 
		texts = question2text(question=questions,transcriber=transcriber,
			input_type = input_type)
	return texts
	
def make_sentiment_file():
	texts = get_sentiment_text()
	output = []
	for x in texts:
		t = x.text.lower()
		if t == 'ik weet het niet' or t == 'ik weet niet': continue
		line = [str(x.pk),x.text,x.response.question.title,str(x.question)]
		output.append('\t'.join(line))
	with open('../sentiment_responses.txt','w') as fout:
		fout.write('\n'.join(output))
	return output
	
		

	
	
