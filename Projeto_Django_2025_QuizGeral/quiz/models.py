from django.db import models
from django.contrib.auth.models import User # Para associar a quem carregou o quiz
from django.db.models.functions import Substr

class QuizCarregado(models.Model):
    """
    Representa um arquivo de quiz que foi carregado pelo usuário.
    """
    usuario_que_carregou = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes_carregados')
    titulo_quiz = models.CharField(max_length=255, help_text="Título do quiz, pode ser o nome do arquivo ou um título personalizado.")
    data_upload = models.DateTimeField(auto_now_add=True, help_text="Data e hora em que o quiz foi carregado.")
    # Poderíamos adicionar um campo para o conteúdo original do arquivo ou um hash dele, se necessário para referência futura.
    # conteudo_original = models.TextField(blank=True, null=True)
    # hash_conteudo = models.CharField(max_length=64, blank=True, null=True, help_text="Hash SHA256 do conteúdo original para identificar duplicatas.")

    def __str__(self):
        return f"{self.titulo_quiz} (Carregado por: {self.usuario_que_carregou.username if self.usuario_que_carregou else 'Desconhecido'})"

    class Meta:
        verbose_name = "Quiz Carregado"
        verbose_name_plural = "Quizzes Carregados"
        ordering = ['-data_upload']

class Questao(models.Model):
    """
    Representa uma única pergunta dentro de um QuizCarregado.
    """
    quiz_carregado = models.ForeignKey(QuizCarregado, on_delete=models.CASCADE, related_name='questoes')
    texto_pergunta = models.TextField(help_text="O texto completo da pergunta.")
    ordem = models.PositiveIntegerField(default=0, help_text="Ordem da pergunta dentro do quiz, conforme o arquivo original.")
    # Se você quiser armazenar a pergunta original como estava no TXT, pode adicionar um campo aqui.

    def __str__(self):
        return f"Questão {self.id} de '{self.quiz_carregado.titulo_quiz}': {self.texto_pergunta[:50]}..."

    class Meta:
        verbose_name = "Questão"
        verbose_name_plural = "Questões"
        ordering = ['quiz_carregado', 'ordem'] # Ordena primeiro pelo quiz, depois pela ordem da questão

class Alternativa(models.Model):
    """
    Representa uma alternativa de resposta para uma Questao.
    """
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='alternativas')
    texto_alternativa = models.CharField(max_length=500, help_text="O texto da alternativa.")
    eh_correta = models.BooleanField(default=False, help_text="Marque se esta é a alternativa correta.")
    ordem = models.PositiveIntegerField(default=0, help_text="Ordem da alternativa dentro da questão, conforme o arquivo original.")

    def __str__(self):
        return f"{self.texto_alternativa} ({'Correta' if self.eh_correta else 'Incorreta'}) para Questão ID {self.questao.id}"

    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ['questao', 'ordem']
