from texts.models import Text, Response, Transcriber
from utils.extract_text import get_all_speech_and_keyboard_text

header = 'wav_filename,transcriber,text,audio_quality,person,question'
header += ',question_description,input_type'
header = header.replace(',','\t')

def text_to_line(t):
    filename = t.audio_filename
    if t.transcriber:
        transcriber = t.transcriber.name.replace(' ','_')
    else:
        transcriber = 'None'
    text = t.text
    audio_quality = t.audio_quality
    person = t.response.person
    q_number = t.response.question.number
    q_desc= t.response.question.description
    input_type = t.input_type.name
    l = [filename,transcriber,text,audio_quality,person,q_number,q_desc]
    l.append(input_type)
    return '\t'.join(map(str,l))

def export_all_responses(save = False, filename = ''):
    if save and filename == '': filename = '../all_responses.tsv'
    output = [header]
    texts = get_all_speech_and_keyboard_text()
    for text in texts:
        line = text_to_line(text)
        output.append(line)
    if save: save_sshoc_transcriptions('\n'.join(output), filename)
    return output


def transcriber_to_lines(transcriber):
    output = []
    texts = Text.objects.filter(transcriber=transcriber)
    for text in texts:
        output.append(text_to_line(text))
    return output

def export_to_tsv(transcriber_names = [],save = False, filename = ''):
    output = [header]
    if not transcriber_names: transcribers = Transcriber.objects.all()
    else:transcribers = [Transcriber.objects.get(n) for n in transcriber_names]
    for transcriber in transcribers:
        lines = transcriber_to_lines(transcriber)
        print(transcriber.name,len(lines))
        output.extend(lines)
    if save:
        if filename: save_sshoc_transcriptions(output,filename)
        else: save_sshoc_transcriptions('\n'.join(output))
    return '\n'.join(output)

def save_sshoc_transcriptions(output,filename = '../sshoc_transcriptions.tsv'):
    print('saving output to:',filename)
    with open(filename,'w') as fout:
        fout.write(output)
        
def read_sshoc_transcriptions(filename = '../sshoc_transcriptions.tsv'):    
    with open(filename) as fin:
        transcriptions = fin.read().split('\n')[1:]
    output = []
    for line in transcriptions:
        output.append(Line(line))
    return output
    

class Line:
    def __init__(self,line):
        self.line = line
        self.set_info()

    def set_info(self):
        for i,name in enumerate(header.split('\t')):
            setattr(self,name,self.line.split('\t')[i])

    def __repr__(self):
        m = ''
        for i,name in enumerate(header.split('\t')):
            value = getattr(self,name)
            m += name + ': ' + value + '\n'
        return m

        
    


