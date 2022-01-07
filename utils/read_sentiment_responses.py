import glob
from statsmodels.stats import inter_rater as irr
from utils import sentiment_bert as sb
from sklearn.metrics import classification_report

fn = glob.glob('../sentiment_responses_*.txt')
rating_dict = {'negative':0,'positive':1,'neutral':2}

def get_reponse():
	f = '../sentiment_responses.txt'
	t = [l.split('\t') for l in open(f).read().split('\n')]
	return t

def _make_automatic_sentiment_responses():
	t = get_reponse()
	pipeline = sb.load_pipeline() 
	for line in t:
		answer = line[1]
		o = sb.str2label(answer)
		label = 'positive' if o[1] == 'pos' else 'negative'
		line.append(label)
	with open('../sentiment_responses_auto-bert.txt','w') as fout:
		fout.write('\n'.join(['\t'.join(line) for line in t]))
	return t
		
	

def get_ratings():
	d = {'all':[]}
	for f in fn:
		name = f.split('_')[-1].split('.')[0]
		t = [line.split('\t') for line in open(f).read().split('\n')]
		ratings = [Rating(line,name) for line in t]
		d[name] = ratings
		d['all'].extend(ratings)
	return d

class RatingStats:
	def __init__(self,ratings = None, exclude_auto = False):
		if not ratings:
			d = get_ratings()
			ratings = d['all']
			if exclude_auto: 
				ratings = [x for x in ratings if 'auto' not in x.rater]
		self.ratings = ratings
		self.raters = list(set([x.rater for x in self.ratings]))
		self.question_numbers=list(set([x.question_number for x in self.ratings]))
		self.pks = list(set([x.pk for x in self.ratings]))
		self._make_rater_dict()
		self._make_question_dict()
		self._make_pk_dict()
		self._make_complete_non_neutral_rating_set()

	def _make_rater_dict(self):
		self.rater_ratings = {}
		for rater in self.raters:
			ratings = [r for r in self.ratings if r.rater == rater]
			self.rater_ratings[rater] = ratings
		self._make_rater_rating_count() 

	def _make_rater_rating_count(self):
		self.rater_rating_count = {}
		self.rater_rating_perc= {}
		for rater in self.raters:
			ratings = self.rater_ratings[rater]
			self.rater_rating_count[rater] = count_ratings(ratings)
			self.rater_rating_perc[rater] = perc_ratings(ratings)

	def _make_question_dict(self):
		self.question_ratings = {}
		for number in self.question_numbers:
			ratings = [r for r in self.ratings if r.question_number ==number]
			self.question_ratings[number] = ratings
		self._make_question_rating_count()

	def _make_question_rating_count(self):
		self.question_rating_count = {}
		self.question_rating_perc= {}
		for number in self.question_numbers:
			ratings = self.question_ratings[number]
			self.question_rating_count[number] = count_ratings(ratings)
			self.question_rating_perc[number] = perc_ratings(ratings)

	def _make_pk_dict(self):
		self.pk_ratings = {}
		for pk in self.pks:
			ratings = [r for r in self.ratings if r.pk ==pk]
			self.pk_ratings[pk] = ratings
		self._make_pk_rating_count()
		
	def _make_pk_rating_count(self):
		self.pk_rating_count = {}
		for pk in self.pks:
			ratings = self.pk_ratings[pk]
			self.pk_rating_count[pk] = count_ratings(ratings)

	def _make_complete_non_neutral_rating_set(self):
		ratings = filter_neutral(self.ratings)
		ratings = filter_questions(ratings)
		self.non_neutral_all_raters = filter_not_all_raters(ratings)

	def _make_fleiss_kappa_dataset(self):
		pks = list(set([r.pk for r in self.non_neutral_all_raters]))
		self.fleiss_kappa_dataset = []
		for pk in pks:
			negative= self.pk_rating_count[pk]['negative']
			positive = self.pk_rating_count[pk]['positive']
			neutral= self.pk_rating_count[pk]['neutral']
			assert neutral == 0
			self.fleiss_kappa_dataset.append([negative,positive])

	def _make_human_auto_dataset(self):
		pks = list(set([r.pk for r in self.non_neutral_all_raters]))
		self.human_auto_dataset = []
		self.human = []
		self.auto = []
		for pk in pks:
			negative, positive = 0, 0
			ratings = [x for x in self.non_neutral_all_raters if x.pk == pk]
			human = [x for x in ratings if 'auto' not in x.rater]
			auto = [x for x in ratings if 'auto' in x.rater]
			counts = count_ratings(human)
			if counts['positive'] > counts['negative']: 
				positive +=1
				self.human.append(1)
			else: 
				negative += 1
				self.human.append(0)
			for x in auto:
				if x.rating == 'positive':
					positive+=1
					self.auto.append(1)
				else: 
					negative +=1
					self.auto.append(0)
			assert negative + positive == 1 + len(auto)
			self.human_auto_dataset.append([negative,positive])
			
	def fleiss_kappa(self):
		if hasattr(self,'_fleiss_kappa'): return self._fleiss_kappa
		if not hasattr(self,'fleiss_kappa_dataset'):
			self._make_fleiss_kappa_dataset()
		self._fleiss_kappa = irr.fleiss_kappa(self.fleiss_kappa_dataset)
		return self._fleiss_kappa

	def fleiss_kappa_human_vs_auto(self):
		if hasattr(self,'_fleiss_kappa_human_vs_auto'):
			return self._fleiss_kappa_human_vs_auto
		if not hasattr(self,'human_auto_dataset'):self._make_human_auto_dataset()
		self._fleiss_kappa_human_vs_auto = irr.fleiss_kappa(self.human_auto_dataset)
		return self._fleiss_kappa_human_vs_auto

	def report(self):
		self.fleiss_kappa_human_vs_auto()
		print(classification_report(self.human,self.auto))
			

class Rating:
	def __init__(self,line, rater):
		self.pk = line[0]
		self.answer = line[1]
		self.question = line[2]
		self.question_number = line[3]
		self.rating = line[4]
		self.rating_number = rating_dict[self.rating]
		self.rater = rater

	def __gt__(self,other):
		return self.question_number > other.question_number

	def __repr__(self):
		m = self.rater + ' | ' + self.question_number + ' | ' + self.rating
		return m
		

def count_ratings(ratings):
	d = {}
	n = len(ratings)
	d['neutral']=sum([1 for r in ratings if r.rating == 'neutral'])
	d['positive']=sum([1 for r in ratings if r.rating == 'positive'])
	d['negative']=sum([1 for r in ratings if r.rating == 'negative'])
	return d

def perc_ratings(ratings):
	d = {}
	n = len(ratings)
	d['neutral']=round(sum([1 for r in ratings if r.rating == 'neutral'])/n*100,2)
	d['positive']=round(sum([1 for r in ratings if r.rating == 'positive'])/n*100,2)
	d['negative']=round(sum([1 for r in ratings if r.rating == 'negative'])/n*100,2)
	return d

def filter_neutral(ratings):
	o = []
	for r in ratings:
		if r.rating == 'neutral': continue
		o.append(r)
	return o

def filter_questions(ratings, question_numbers = [13,16]):
	if type(question_numbers) == int:question_numbers = [question_numbers]
	question_numbers = list(map(str,question_numbers))
	o = []
	for r in ratings:
		if r.question_number not in question_numbers: 
			o.append(r)
	return o

def filter_not_all_raters(ratings):
	o = []
	nraters = len(list(set([r.rater for r in ratings])))
	pks = list(set([r.pk for r in ratings]))
	for pk in pks:
		found = [r for r in ratings if r.pk == pk]
		if len(found) == nraters: o.extend(found)
	return o

def ratings_to_rating_numbers(ratings):
	o = [] 
	for rating in ratings:
		o.append(rating.rating_number)
	return o
