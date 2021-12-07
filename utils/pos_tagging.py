content_pos = 'ADJ,BW,N,VNW,WW'.split(',')

try:
	import frog
	frogger = frog.Frog(frog.FrogOptions(parser=False))
except: print('could not load frog, start lamachine to use frog')


def text_to_content_words(text):
	if not text.text:
		print('no text:',[text.text])
		text.content_words = ''
		text.save()
	try:output = frogger.process(text.text)
	except:
		print('could not do pos tagging')
		print('doing nothing')
		return	
	print('text:',text.text)
	print('frog output:',output)
	content_words = []
	for word in output:
		pos = word['pos'].split('(')[0]
		print('pos:',pos)
		if pos in content_pos: content_words.append(word['text'])
	print('content words:',content_words)
	text.content_words = ' '.join(content_words)
	text.save()
			
	
