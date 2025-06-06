import random
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from .forms import UploadFileForm
from .parser import parse_quiz_file
from django.views.decorators.csrf import csrf_exempt
from .models import Questao, Alternativa, QuizCarregado
from .forms import UploadFileForm

@transaction.atomic
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                file_content = uploaded_file.read().decode('utf-8')
                questions = parse_quiz_file(file_content)

                if not questions:
                    form.add_error('file', 'Não foi possível extrair perguntas do arquivo.')
                    return render(request, 'quiz/upload_form.html', {
                        'form': form,
                        'error_message': 'Formato de arquivo inválido ou arquivo vazio.'
                    })

                # Limita para exatamente 30 questões se necessário
                if len(questions) > 30:
                    questions = random.sample(questions, 30)

                # Cria o registro do quiz no banco
                quiz = QuizCarregado.objects.create(
                    titulo_quiz=uploaded_file.name,
                    usuario_que_carregou=request.user if request.user.is_authenticated else None
                )

                # Salva cada questão e suas alternativas
                for ordem, question_data in enumerate(questions, 1):
                    questao = Questao.objects.create(
                        quiz_carregado=quiz,
                        texto_pergunta=question_data['text'],
                        ordem=ordem
                    )
                    
                    # Salva as alternativas
                    for ordem_alt, choice in enumerate(question_data['choices'], 1):
                        Alternativa.objects.create(
                            questao=questao,
                            texto_alternativa=choice['text'],
                            eh_correta=choice['is_correct'],
                            ordem=ordem_alt
                        )

                # Salva as questões na sessão para o quiz
                request.session['quiz_questions'] = questions
                request.session['answered_question_indices'] = []
                request.session['score'] = 0
                request.session['quiz_id'] = quiz.id

                messages.success(request, 'Quiz carregado com sucesso!')
                return redirect('quiz:start_quiz')

            except UnicodeDecodeError:
                form.add_error('file', 'O arquivo não parece ser um arquivo de texto UTF-8 válido.')
                return render(request, 'quiz/upload_form.html', {
                    'form': form,
                    'error_message': 'Erro de codificação do arquivo.'
                })
            except Exception as e:
                form.add_error('file', f'Erro ao processar o arquivo: {e}')
                return render(request, 'quiz/upload_form.html', {
                    'form': form,
                    'error_message': f'Erro ao processar o arquivo.'
                })
    else:
        form = UploadFileForm()
    return render(request, 'quiz/upload_form.html', {'form': form})

def get_random_question_data(questions, answered_indices):
    available_indices = [i for i, _ in enumerate(questions) if i not in answered_indices]
    if not available_indices:
        return None

    random_index = random.choice(available_indices)
    question_data = questions[random_index]
    return {"index": random_index, **question_data}

def start_quiz(request):
    questions = request.session.get('quiz_questions')
    quiz_id = request.session.get('quiz_id')
    
    if not questions or not quiz_id:
        messages.error(request, 'Por favor, carregue um arquivo de quiz primeiro.')
        return redirect('quiz:upload_quiz_file')

    # Carrega o quiz do banco
    try:
        quiz = QuizCarregado.objects.get(id=quiz_id)
        request.session['answered_question_indices'] = []
        request.session['score'] = 0

        first_question_data = get_random_question_data(questions, [])
        
        if not first_question_data:
            messages.error(request, 'Nenhuma pergunta encontrada no quiz carregado.')
            return render(request, 'quiz/quiz_page.html', {
                'error_message': 'Nenhuma pergunta encontrada no quiz carregado.'
            })

        return render(request, 'quiz/quiz_page.html', {
            'question_data': first_question_data,
            'total_questions': len(questions)
        })
    except QuizCarregado.DoesNotExist:
        messages.error(request, 'Quiz não encontrado. Por favor, carregue novamente.')
        return redirect('quiz:upload_quiz_file')

@csrf_exempt
def submit_answer(request):
    if request.method == 'POST':
        questions = request.session.get('quiz_questions')
        answered_indices = request.session.get('answered_question_indices', [])
        score = request.session.get('score', 0)

        if not questions:
            return JsonResponse({'error': 'Quiz não iniciado ou sessão expirada.'}, status=400)

        question_index = int(request.POST.get('question_index'))
        selected_choice_text = request.POST.get('answer')

        question_data = questions[question_index]
        is_correct = False
        correct_answer_text = ""
        
        # Normaliza as strings para comparação
        selected_choice_text = selected_choice_text.strip().lower() if selected_choice_text else ""
        
        print(f"Questão índice: {question_index}")
        print(f"Texto da questão: {question_data['text'][:50]}...")
        print(f"Resposta selecionada: {selected_choice_text}")
        
        for choice in question_data['choices']:
            choice_text = choice['text'].strip().lower() if choice['text'] else ""
            
            if choice['is_correct']:
                correct_answer_text = choice['text']
                print(f"Resposta correta encontrada: {choice_text}")
                
            if choice['is_correct'] and choice_text == selected_choice_text:
                is_correct = True
                print("Resposta marcada como correta!")
                break

        if not is_correct:
            print(f"Resposta incorreta. Esperado: {correct_answer_text.strip().lower()}")

        response_data = {'correct': is_correct, 'correct_answer': correct_answer_text}
        
        # Atualiza o score apenas se ainda não respondeu esta questão
        if is_correct and question_index not in answered_indices:
            score += 1
            answered_indices.append(question_index)
            response_data['feedback_message'] = "Correto!"
        else:
            if question_index not in answered_indices:
                answered_indices.append(question_index)
            response_data['feedback_message'] = f"Incorreto. A resposta correta é: {correct_answer_text}"
          # Verifica se já respondeu 30 questões
        if len(answered_indices) >= 30:
            response_data['quiz_finished'] = True
            response_data['score'] = score
            response_data['total_questions'] = 30
        else:
            # Busca a próxima questão se ainda não completou 30
            next_question = get_random_question_data(questions, answered_indices)
            if next_question:
                response_data['next_question'] = next_question

        request.session['answered_question_indices'] = answered_indices
        request.session['score'] = score

        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Método de requisição inválido.'}, status=405)

def upload_quiz_file_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                file_content = uploaded_file.read().decode('utf-8')
                parsed_quiz_data = parse_quiz_file(file_content)  # Using the existing parser function

                if not parsed_quiz_data:
                    messages.error(request, "O arquivo está vazio ou mal formatado.")
                    return redirect('quiz:upload_quiz_file') # Ou renderizar o form com erro

                # Preparar dados para a sessão (aplicar limite de 30 questões, se houver mais)
                questions_for_session = list(parsed_quiz_data) # Copiar para evitar modificar o original se random.sample modificar
                if len(questions_for_session) > 30:
                    questions_for_session = random.sample(questions_for_session, 30)
                # Se questions_for_session estiver vazio após o parse, o 'if not parsed_quiz_data' já tratou.

                with transaction.atomic(): # Garante que todas as operações de DB sejam um sucesso ou falhem juntas
                    # 1. Criar o QuizCarregado
                    novo_quiz = QuizCarregado.objects.create(
                        usuario_que_carregou=request.user if request.user.is_authenticated else None,
                        titulo_quiz=uploaded_file.name # Ou um título fornecido pelo usuário
                    )

                    #2. Iterar sobre as perguntas parseadas e criar objetos Questao e Alternativa
                    for i, questao_data in enumerate(parsed_quiz_data):
                        # Ajuste para corresponder à estrutura do parser: 'text' para pergunta, 'choices' para alternativas
                        nova_questao = Questao.objects.create(
                            quiz_carregado=novo_quiz,
                            texto_pergunta=questao_data['text'], # Mudança de 'pergunta' para 'text'
                            ordem=i
                        )

                        # Ajuste para corresponder à estrutura do parser: 'choices' e 'is_correct'
                        if not questao_data.get('choices') or not any(alt.get('is_correct') for alt in questao_data['choices']):
                            # Se uma pergunta não tiver alternativas ou nenhuma correta, pode ser um erro de formatação
                            # Você pode optar por levantar um erro aqui e cancelar a transação
                            raise ValueError(f"A pergunta '{questao_data['text'][:50]}...' não possui alternativas válidas ou uma alternativa correta.")

                        for j, alt_data in enumerate(questao_data['choices']): # Mudança de 'alternativas' para 'choices'
                            Alternativa.objects.create(
                                questao=nova_questao,
                                texto_alternativa=alt_data['text'], # Mudança de 'texto' para 'text'
                                eh_correta=alt_data['is_correct'], # Mudança de 'correta' para 'is_correct'
                                ordem=j
                            )

                # Se o salvamento no DB foi bem-sucedido, configurar a sessão para o quiz.
                request.session['quiz_questions'] = questions_for_session
                # 'answered_question_indices' e 'score' serão inicializados por start_quiz.

                messages.success(request, f"Quiz '{novo_quiz.titulo_quiz}' carregado, salvo no banco e pronto para iniciar!")
                return redirect('quiz:start_quiz') # Redireciona para iniciar o quiz

            except UnicodeDecodeError:
                messages.error(request, 'O arquivo não parece ser um arquivo de texto UTF-8 válido.')
                return redirect('quiz:upload_quiz_file')
            except ValueError as ve: # Erro de validação do parser ou da estrutura
                messages.error(request, f"Erro ao processar o arquivo: {ve}")
                return redirect('quiz:upload_quiz_file')
            except Exception as e:
                # Lidar com outros erros (ex: erro de decodificação, erro inesperado no parser)
                messages.error(request, f"Ocorreu um erro inesperado ao carregar o quiz: {e}")
                return redirect('quiz:upload_quiz_file')
    else:
        form = UploadFileForm()
    return render(request, 'quiz/upload_form.html', {'form': form})
