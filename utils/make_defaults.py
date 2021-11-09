import sys
from texts.models import Inputtype, Transcriber
from .color import color as c

asr_systems = 'questfox,conversational_dialogues,oral_history,parliamentary_speeches'
asr_systems = asr_systems.split(',')
human_transcribers = []

def add_transcribers():
	names = asr_systems + human_transcribers 
	human = [False] *len(asr_systems) + [True] * len(human_transcribers)
	for h, name in zip(human,names):
		save_model(Transcriber, {'name':name,'human':h}, 'name')


input_types = 'speech,keyboard'.split(',')

def add_inputtype():
	for name in input_types:
		save_model(Inputtype,{'name':name},'name')


def save_model(model, input_dict, check_fieldname = ''):
		model_name = model._meta.model_name
		print('model:',model_name,'input:',input_dict,'check:',check_fieldname)
		name = ''
		if check_fieldname:
			check = {check_fieldname: input_dict[check_fieldname]}
			name = input_dict[check_fieldname]
			queryset= model.objects.filter(**check)
			if queryset:
				print(c(name,'blue'),'already present in database')
				return queryset[0]
		if not name: name = list(input_dict.values())[0]
		try:
			instance = model(**input_dict)
			instance.save()
		except: print(c('could not save','red'),c(name,'blue'), sys.exc_info())
		else: print('saved:',c(name,'blue'))
		return instance
	

