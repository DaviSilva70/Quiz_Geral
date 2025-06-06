from django.urls import path
from . import views

app_name = 'quiz'  # Define um namespace para estas URLs

urlpatterns = [
    # Rota para a página de upload do arquivo TXT
    path('upload/', views.upload_file, name='upload_quiz_file'),

    # Rota para iniciar o quiz (depois que o arquivo foi carregado)
    path('iniciar/', views.start_quiz, name='start_quiz'),

    # Endpoint para processar respostas
    path('responder/', views.submit_answer, name='submit_answer'),
    
    # Rota raiz do app 'quiz', aponta para a view de upload
    path('', views.upload_file, name='index'),
]
