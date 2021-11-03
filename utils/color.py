RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
ENDC = '\033[0m'

colors = {'blue':BLUE,'red':RED,'cyan':CYAN,'green':GREEN,'bold':BOLD}
colors.update({'underline':UNDERLINE,'end':ENDC})

def color(s, command ='blue'):
	if type(command) == list: command = ','.join(command)
	command = command.lower()
	command = command.split(',')
	s = str(s)
	o = ''
	for c in command:
		if c not in colors.keys(): 
			print(c,'not found')
			continue
		o += colors[c]
	return o + s + ENDC
		
	
