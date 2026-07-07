from ai_app.speech.bilingual import merge_tutor_transcripts, tutor_transcript_label

ru = 'Можешь поговорить со мной сегодня'
en = 'can you talk to me today'
merged = merge_tutor_transcripts(ru, en)
print('merged', repr(merged))
print('label', tutor_transcript_label(merged))
