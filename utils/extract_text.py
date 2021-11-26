from texts.models import Variable,Session,Response,Inputtype,Person,Text,Question
from texts.models import Transcriber

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

def question2text(question = 'all', transcriber = 'questfox',exclude_q8 = True):
	'''get all text instance ordered by person.
	by default excluded question 8 because this has no content (test sentence)
	'''
	question = _handle_question(question, exclude_q8)
	transcriber = _handle_transcriber(transcriber)
	t = Text.objects.filter(response__question__number__in = question)
	t = t.filter(transcriber__name = transcriber)
	return t.order_by('response__person__number')

	
def question2str(question='all',transcriber='questfox', exclude_q8 = True, 
	show_person = True, show_question = True, show_transcriber = False,
	show_audio_filename = False, show_audio_quality = False):
	'''creates a str output of texts based on question set.
	'''
	output = []
	texts = question2text(question,transcriber,exclude_q8)
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
	
