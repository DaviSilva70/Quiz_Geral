# quiz/admin.py
from django.contrib import admin
from .models import QuizCarregado, Questao, Alternativa

admin.site.register(QuizCarregado)
admin.site.register(Questao)
admin.site.register(Alternativa)
