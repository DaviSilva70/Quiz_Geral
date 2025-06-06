# quiz/forms.py
from django import forms

class UploadFileForm(forms.Form):
    # Formulário para upload de arquivo TXT do quiz
    file = forms.FileField(label='Selecione o arquivo TXT do quiz')

