from django import forms

from .models import Word


class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = (
            'english',
            'translation',
            'example',
            'difficulty',
        )

        widgets = {
            'english': forms.TextInput(attrs={
                'placeholder': 'Например: apple',
            }),
            'translation': forms.TextInput(attrs={
                'placeholder': 'Например: яблоко',
            }),
            'example': forms.Textarea(attrs={
                'placeholder': 'Например: I eat an apple every day.',
                'rows': 4,
            }),
        }
