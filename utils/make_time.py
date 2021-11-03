def make_time(seconds):
	seconds = int(seconds)
	h = str(seconds // 3600)
	seconds = seconds % 3600
	m = str(seconds // 60)
	s = str(seconds % 60)
	if len(h)  == 1: h = '0' + h
	if len(m) == 1: m = '0' + m 
	if len(s) == 1: s = '0' + s
	return ':'.join([h,m,s,])
