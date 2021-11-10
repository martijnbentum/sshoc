from django.apps import apps
from transformers import pipeline
import pickle
# from openpyxl import Workbook
from xlsxwriter import Workbook

from .color import color

labels ='loc,per,org,misc'.split(',')
label2color = {'loc':'blue','per':'red','org':'cyan','misc':'magenta'}


def download_pipeline():
	'''download pipeline from huggingface.'''
	return pipeline('ner', 
		model='wietsedv/bert-base-dutch-cased-finetuned-conll2002-ner')

def load_pipeline():
	'''opens a pickled pipeline locally.'''
	fin = open('ner_bertje','rb')
	p = pickle.load(fin)
	return p

def apply_pipeline(t, pipeline = None):
	if pipeline == None: pipeline = load_pipeline()
	return pipeline(t)

def _handle_entity_excel(entity,string,temp,index,wb):
	label = entity['entity'].split('-')[-1]
	color_name = label2color[label]
	start,end = entity['start'], entity['end']
	temp.append(string[index:start])
	temp.append(wb.add_format({'color':color_name,'bold':True}))
	temp.append(string[start:end])
	index = end
	return temp,index
	

def _handle_entity_string(entity,string, temp, index,wb =None):
	label = entity['entity'].split('-')[-1]
	color_name = label2color[label]
	start,end = entity['start'], entity['end']
	temp += string[index:start]
	temp += color(string[start:end],color_name)
	index = end
	return temp,index

def _handle_output(output,string, handle = 'to_string',wb =None):
	if 'excel' in handle and wb: 
		handle_entity = _handle_entity_excel
		temp = []
	else:
		handle = _handle_entity_string
		temp = ''
	print('---\n',string,2)
	index = 0
	for entity in output:
		print(entity,3)
		temp,index = handle_entity(entity,string,temp,index,wb)
	if 'excel' in handle: temp.append( string[index:])
	else: temp += string[index:]
	string = temp
	print(string,4)
	return string
	
def label_str(string,pipeline = None, handle = 'to_string',wb = None):
	string = string.replace('\n',' ').replace('\t',' ')
	o = apply_pipeline(string,pipeline)
	string = _handle_output(o,string, handle =handle, wb=wb)
	return string
		
def label_text(text,pipeline = None, handle = 'to_string',wb = None):
	print('response:',text.response, text.audio_filename)
	return label_str(text.text, pipeline, handle=handle, wb=wb)

def label_texts(texts,pipeline = None, handle = 'to_string', wb = None):
	pipeline = load_pipeline()
	output = []
	for text in texts:
		output.append( label_text(text,pipeline, handle=handle , wb=wb) )
	return output

def make_string_output(questions = []):
	if questions == []: questions = Question.objects.filter(number__gte = 9)
	else: questions = Question.objects.filter(number__in = questions)
	output = []
	for q in questions:
		print('question:',q)
		o.extend(label_texts(q.texts(), p, handle= 'to_excel', wb =wb))
	return '\n\n'.join(o)
			

def _o2sheet(o,sheet,label = ''):
	print(type(o),333,o)
	for row,line in enumerate(o):
		print([line],1,['A' + str(row+1)])
		l = ['A' + str(row+1)] + line
		if len(line) > 1:sheet.write_rich_string(*l)
		else: sheet.write_string(*l)
			

	
def make_xlsx(questions = [], filename = 'ner.xlsx'):
	if filename:
		if not filename.endswith('.xlsx'): filename += '.xslx'
	p = load_pipeline()
	Question = apps.get_model('texts','question')
	if questions == []: questions = Question.objects.filter(number__gte = 9)
	else: questions = Question.objects.filter(number__in = questions)
	wb = Workbook(filename)
	all_o = []
	for q in questions:
		print('question:',q)
		o = label_texts(q.texts(), p, handle= 'to_excel', wb =wb)
		all_o.extend(o)
		sheet = wb.add_worksheet(str(q.number))
		_o2sheet(o,sheet,q.description)
	sheet = wb.add_worksheet('all')
	_o2sheet(all_o,sheet,q.description)
	if filename: wb.close()
	return wb
		
		
