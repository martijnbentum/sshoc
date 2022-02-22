from django.db import models
from utils.make_time import make_time
from utils.color import color 

# Create your models here.

class Person(models.Model):
	'''participant answering question.'''
	number = models.IntegerField(unique = True, default =None)

	def __repr__(self):
		return str(self.number)
	def __str__(self):
		return self.__repr__()

class Question(models.Model):
	'''question the text/response belongs to.'''
	number = models.IntegerField(unique = True, default =None)
	title = models.CharField(max_length=300,default ='') 
	description = models.TextField(default='',blank=True, null=True)
	condition = models.CharField(max_length=300,default ='') 

	def __repr__(self):
		return str(self.number) + ':' + self.description + ' | ' + self.condition
	def __str__(self):
		return self.__repr__()

	def texts(self,transcriber_name = 'questfox'):
		responses = self.response_set.all()
		texts = []
		tn = transcriber_name
		for response in responses:
			texts.extend(list(response.text_set.filter(transcriber__name=tn)))
		return texts

	@property
	def persons(self):
		persons= []
		responses = self.response_set.all()
		for response in responses:
			persons.append(response.person)
		return list(set(persons))

	@property
	def find_other_condition(self):
		'''Find the same question for the other condition.
		identical questions where asked for text and audio conditions
		'''
		for q in Question.objects.all():
			if q.condition != self.condition and q.description == self.description:  
				return q

	@property
	def column_index(self):
		'''find the column index of this question in the NIDI file'''
		for v in Variable.objects.all():
			if 'Q' in v.name and v.name.endswith('Q1'): 
				if int(v.name.split('Q')[1]) == self.number: return v.column_index

class Inputtype(models.Model):
	'''whether input was given via keyboard or speech.'''
	name = models.CharField(max_length=300,default ='', unique = True) 

	def __repr__(self):
		return self.name

class Transcriber(models.Model):
	'''speech input is transcribed by multiple ASR systems and human
	transcriber.
	'''
	name = models.CharField(max_length=300,default ='', unique = True)
	human = models.BooleanField(default=False)

	def __repr__(self):
		return self.name




class Session(models.Model):
	'''participants entered a questionaire online, this was recorded
	in sessions. A person could complete the questionaire in multiple sessions.
	questions can be answered multiple times by a participant.
	'''
	values= models.TextField(default='',blank=True, null=True)
	session_date = models.DateField(default = None)
	row_index = models.IntegerField(unique = True, default =None)
	duration= models.IntegerField(default =None)

	def __repr__(self):
		m = color(self.row_index,'blue') + ' | ' + str(self.session_date)
		m += ' | pp-id: ' + str(eval(self.values)[4])
		m += ' | duration: ' + make_time(self.duration)
		return m

	@property
	def person(self):
		return int(eval(self.values)[4])

class Response(models.Model):
	''' response to specific question linked to a person question and audio file.
	text_set links the the set of transcriptions if speech input_type
	otherwise it links to the keyboard entered text (there will only be one text)
	audio quality rate the quality of the recording 
	(not present for all responses)
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	question = models.ForeignKey(Question,**dargs)
	person = models.ForeignKey(Person,**dargs)
	input_type= models.ForeignKey(Inputtype,**dargs)
	audio_filename = models.CharField(max_length=1000,default ='')
	audio_quality = models.CharField(max_length=50,default ='')
	response_date = models.DateField(default = None)
	row_index = models.IntegerField(default =None)
	session = models.ForeignKey(Session,**dargs)

	def __repr__(self):
		return self.question.__repr__() + ' | ' + self.person.__repr__()
	def __str__(self):
		return self.__repr__()

	@property
	def transcribers(self):
		return [t.transcriber.name for t in self.text_set.all() if t.transcriber]

class Variable(models.Model):
	'''gives some information about the questions.'''
	name = models.CharField(max_length=30,default ='')
	title= models.CharField(max_length=300,default ='')
	value= models.CharField(max_length=1000,default ='')
	column_index= models.IntegerField(unique = True, default =None)

	def __repr__(self):
		return self.name + ' | ' + self.title


class Text(models.Model):
	'''answer to a specific question from a person.
	for speech input_type there are multiple transcriptions
	alternate_transcriptions links to these.
	'''
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	text = models.TextField(default='',blank=True, null=True)
	transcriber= models.ForeignKey(Transcriber,**dargs)
	response = models.ForeignKey(Response,**dargs)
	input_type= models.ForeignKey(Inputtype,**dargs)
	include = models.BooleanField(default=True)
	content_words= models.TextField(default='',blank=True, null=True)

	def __repr__(self):
		m = self.transcriber.__repr__() + ' | ' + self.text[:20] 
		if len(self.text) >= 20: m += '...'
		m += " | " + str(self.word_count)
		return m
	def __str__(self):
		return self.__repr__()

	@property
	def person(self):
		return self.response.person.number
	@property
	def question(self):
		return self.response.question.number
	@property
	def audio_quality(self):
		return self.response.audio_quality
	@property
	def audio_filename(self):
		return self.response.audio_filename
	@property
	def alternate_transcriptions(self):
		other_texts = self.response.text_set.all()
		output = [t for t in other_texts if t != self]
		return output

	@property
	def word_count(self):
		return len(self.text.split(' '))

	def get_content_words(self, pos_tagging =None):
		if not pos_tagging:from utils import pos_tagging as pt
		else: pt = pos_tagging
		if self.content_words == '':
			print('pos tagging to find content words')
			pt.text_to_content_words(self)

	@property
	def content_word_count(self):
		if not self.content_words: self.get_content_words()
		return len(self.content_words.split(' '))

	def check_include(self,min_nwords = 3, only_contain_stop_words = None):
		include = True
		if not self.text: include = False
		elif self.text.lower() == 'weet ik niet':include = False
		elif self.word_count < min_nwords: include = False
		elif check_only_contain_stop_words(self.text): include = False
		if include != self.include:
			self.include =include 
			self.save()


def check_only_contain_stop_words(words,stop_words= None):
	if stop_words == None:
		from stop_words import get_stop_words
		stop_words = get_stop_words('dutch')
	if type(words) == str: words = words.split(' ')
	for word in words:
		if word.lower() not in stop_words: return False
	return True




#need for migration purposes
class rep:
	pass
