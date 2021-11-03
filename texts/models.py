from django.db import models

# Create your models here.

class Question(models.Model):
	name = models.CharField(max_length=300,default ='') 

class InputType(models.Model):
	name = models.CharField(max_length=300,default ='') 

class Transcriber(models.Model):
	name = models.CharField(max_length=300,default ='')
	human = models.BooleanField(default=False)

class Text(models.Model):
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	text = models.TextField(default='',blank=True, null=True)
	input_type = models.ForeignKey(InputType,**dargs)
	Transcriber= models.ForeignKey(Transcriber,**dargs)

class Response(models.Model):
	question = models.ForeignKey(Question,**dargs)
	person = models.ForeignKey(Person,**dargs)
	texts = models.ManyToManyField(Text,blank=True, default= None)
	audio_filename = models.CharField(max_length=1000,default ='')
