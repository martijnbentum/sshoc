from datetime import datetime
from openpyxl import Workbook
from openpyxl import load_workbook
from .make_defaults import save_model
from texts.models import Variable, Session

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
	return datetime(d.year,d.month,d.day,t.hour,t.minute,t.second)
		

def read_in_text():
	qf = Transcriber.objects.get('questfox')
	cd = Transcriber.objects.get('conversational_dialogues')
	oh = Transcriber.objects.get('oral_history')
	ps = Transcriber.objects.get('parliamentary_speeches')
	wb = open_text_xlsx()
	audio_fn_dict = make_audio_fn_dict(wb = wb)
	sheet = wb['Matched Text Entries']
	for i,line in enumerate(list(sheet.values)[1:]):
		response_date = _add_date_and_time(line[0],line[1]
		pp_id = line[4]
		question_number = line[7]
		audio_fn = line[8]
		_, tqf, tcd, toh, tps, audio_quality = audio_fn_dict[audio_fn]
			
	
	
