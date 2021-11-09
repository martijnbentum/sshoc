from django.db import connection
from datetime import datetime
from openpyxl import Workbook
from openpyxl import load_workbook
from .make_defaults import save_model
from texts.models import Variable,Session,Response,Inputtype,Person,Text,Question
from texts.models import Transcriber

def open_nidi_xlsx():
	return load_workbook('../NIDI-voice-recorded-interviews-audio-transcripts.xlsx')

def open_text_xlsx():
	return load_workbook('../Text - Audio Matching.xlsx')

def handle_time(date_cell,time_cell):
	'''converts a date and time cell into a datetime object
	date_cell should have the following formate: 2021-04-17
	time_cell should have the following formate: 15:34:46
	'''
	s = date_cell + ' ' + time_cell
	return datetime.strftime(s,'%Y-%m-%d %H:%M:%S')

def read_in_variables():
	wb = open_nidi_xlsx()
	sheet = wb['Variables']
	for i,line in enumerate(list(sheet.values)[1:]):
		name, title, value = line[:3] 
		if not name: break
		if not title: title = ''
		if not value: value = ''
		d = {'name':name,'title':title,'value':value,'column_index':i}
		save_model(Variable,d,'name')

def session_header():
	wb = open_nidi_xlsx()
	sheet = wb['Response Data']
	return list(sheet.values)[0]
		
def read_in_session():
	wb = open_nidi_xlsx()
	sheet = wb['Response Data']
	for i,line in enumerate(list(sheet.values)[1:]):
		line = list(line)
		session_date = line[0]
		line[0] = str(line[0])
		duration = line[1]
		values = str(line)
		d = {'session_date':session_date,'values':values,'row_index':i}
		d.update({'duration':duration})
		save_model(Session,d,'row_index')

def make_audio_fn_dict(wb = None):
	if not wb: wb = open_text_xlsx()
	sheet = wb['audio_for_review']
	d = {}
	for i,line in enumerate(list(sheet.values)[1:]):
		d[line[0]] = line[:6]
	return d
	
def _add_date_and_time(date, time):
	d, t = date, time
	print('date',d,'time',t)
	return datetime(d.year,d.month,d.day,t.hour,t.minute,t.second)

def get_person(person_number):
	person_number = int(person_number)
	instance = save_model(Person,{'number':person_number},'number')
	return instance

def get_question(question_number):
	question_number = int(question_number)
	instance = save_model(Question,{'number':question_number},'number')
	return instance

def get_transcriber(name, human = False):
	instance = save_model(Transcriber,{'name':name,'human':human},'name')
	return instance

def make_text(text, transcriber, response):
	'''makes a new text instance based on a text and a transcriber.'''
	d ={'text':text,'transcriber':transcriber,'response':response}
	instance = save_model(Text,d)
	return instance
	
def _make_texts(tqf,tcd,toh,tps, response):
	'''special function to make texts instances form the 4 asr systems used
	to decode the audio.
	'''
	qf = Transcriber.objects.get(name ='questfox')
	cd = Transcriber.objects.get(name ='conversational_dialogues')
	oh = Transcriber.objects.get(name ='oral_history')
	ps = Transcriber.objects.get(name ='parliamentary_speeches')
	scribes = [qf,cd,oh,ps]
	texts = [tqf,tcd,toh,tps]
	return [make_text(t,s,response) for t,s in zip(texts,scribes)]
		
def _make_response(question,person,input_type,audio_filename,audio_quality,
	response_date,row_index):
	print('making response:',question,person)
	d = {'question':question,'person':person,'input_type':input_type}
	d.update({'audio_filename':audio_filename,'audio_quality':audio_quality})
	d.update({'response_date':response_date,'row_index':row_index})
	instance = save_model(Response,d,'row_index')
	return instance

def _line_ok(line):
	return line[0] != None


def read_in_text_audio_matching(clean_db = False):
	if clean_db: 
		Response.objects.all().delete()
		Text.objects.all().delete()
		connection.cursor().execute("VACUUM")
	qf = Transcriber.objects.get(name ='questfox')
	speech = Inputtype.objects.get(name = 'speech')
	wb = open_text_xlsx()
	audio_fn_dict = make_audio_fn_dict(wb = wb)
	sheet = wb['Matched Text Entries']
	for i,line in enumerate(list(sheet.values)[1:]):
		if not _line_ok(line): continue
		print('line',line)
		response_date = _add_date_and_time(line[0],line[1])
		person = get_person(line[4])
		question = get_question(line[7])
		audio_fn = line[8]
		audio_quality = ''
		response = _make_response(question,person,speech,audio_fn,audio_quality,
			response_date,i)
		if audio_fn in audio_fn_dict.keys():
			_, tqf, tcd, toh, tps, audio_quality = audio_fn_dict[audio_fn]
			texts = _make_texts(tqf,tcd,toh,tps,response)
		else:
			texts = [make_text(line[5],qf, response)]
			print('could not find:',audio_fn)

			
	
	
