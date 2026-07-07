import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from ai_app.speech.bilingual import (
    merge_tutor_transcripts,
    merge_whisper_tutor_transcript,
    merge_code_switch_transcript,
    looks_like_phonetic_russian_latin,
    tutor_transcript_label,
)

en = 'I like to puta shestertva t citat knigi'
ru = ''
ru2 = 'я люблю путешествовать и читать книги'

for w in en.split():
    bare = w.lower().strip(".,'")
    print(w, 'phonetic', looks_like_phonetic_russian_latin(bare))

print('code_switch empty ru:', merge_code_switch_transcript(ru, en))
print('code_switch with ru:', merge_code_switch_transcript(ru2, en))
print('whisper merge:', merge_whisper_tutor_transcript(en))
print('merge empty ru:', merge_tutor_transcripts(ru, en))
print('merge with ru:', merge_tutor_transcripts(ru2, en))
print('label empty:', tutor_transcript_label(merge_tutor_transcripts(ru, en)))
