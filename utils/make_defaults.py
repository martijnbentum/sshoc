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


def save_model(model, input_dict, check_fieldname):
		check = {check_fieldname: input_dict[check_fieldname]}
		name = input_dict[check_fieldname]
		if model.objects.filter(**check):
			print(c(name,'blue'),'already present in database')
			return
		try:
			x = model(**input_dict)
			x.save()
		except: print(c('could not save','red'),c(name,'blue'), sys.exc_info())
		else: print('saved:',c(name,'blue'))
	

