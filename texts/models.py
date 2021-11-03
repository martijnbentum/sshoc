from django.db import models
from utils.make_time import make_time
from utils.color import color 

# Create your models here.
class rep:
	def __repr__(self):
		return self.name


class Person(models.Model,rep):
	name = models.CharField(max_length=300,default ='', unique = True) 

	def __repr__(self):
		return self.name

class Question(models.Model,rep):
	name = models.CharField(max_length=300,default ='', unique = True) 
	number = models.IntegerField(unique = True, default =None)

	def __repr__(self):
		return self.name

class Inputtype(models.Model,rep):
	name = models.CharField(max_length=300,default ='', unique = True) 

	def __repr__(self):
		return self.name

class Transcriber(models.Model):
	name = models.CharField(max_length=300,default ='', unique = True)
	human = models.BooleanField(default=False)

	def __repr__(self):
		return self.name

class Text(models.Model):
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	text = models.TextField(default='',blank=True, null=True)
	Transcriber= models.ForeignKey(Transcriber,**dargs)

class Response(models.Model):
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	question = models.ForeignKey(Question,**dargs)
	person = models.ForeignKey(Person,**dargs)
	input_type= models.ForeignKey(Inputtype,**dargs)
	texts = models.ManyToManyField(Text,blank=True, default= None)
	audio_filename = models.CharField(max_length=1000,default ='')
	response_date = models.DateField(default = None)

class Session(models.Model):
	values= models.TextField(default='',blank=True, null=True)
	session_date = models.DateField(default = None)
	row_index = models.IntegerField(unique = True, default =None)
	duration= models.IntegerField(default =None)

	def __repr__(self):
		m = color(self.row_index,'blue') + ' | ' + str(self.session_date)
		m += ' | pp-id: ' + str(eval(self.values)[4])
		m += ' | duration: ' + make_time(self.duration)
		return m

class Variable(models.Model):
	name = models.CharField(max_length=30,default ='')
	title= models.CharField(max_length=300,default ='')
	value= models.CharField(max_length=1000,default ='')
	column_index= models.IntegerField(unique = True, default =None)

	def __repr__(self):
		return self.name + ' | ' + self.title
