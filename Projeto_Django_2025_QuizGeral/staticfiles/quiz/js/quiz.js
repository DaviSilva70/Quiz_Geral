document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const elements = {
        questionBlock: document.getElementById('question-block'),
        feedbackArea: document.getElementById('feedback-area'),
        nextQuestionBtn: document.getElementById('next-question-btn'),
        quizFinishedMessage: document.getElementById('quiz-finished-message'),
        currentScoreEl: document.getElementById('current-score'),
        answeredCountEl: document.getElementById('answered-count'),
        totalQuestionsDisplayEl: document.getElementById('total-questions-display')
    };

    // Estado do quiz
    const quizState = {
        score: 0,
        answeredCorrectlyCount: 0,
        nextQuestionData: null,
        totalQuestions: parseInt(elements.totalQuestionsDisplayEl?.textContent || '0')
    };

    // Esconde o botão de próxima questão inicialmente
    if (elements.nextQuestionBtn) {
        elements.nextQuestionBtn.style.display = 'none';
    }

    // Se não houver bloco de questões, mostra mensagem adequada
    if (!elements.questionBlock && !document.querySelector('.alert-danger')) {
        const quizArea = document.querySelector('.card-body');
        if(quizArea) {
            quizArea.innerHTML = `
                <div class="alert alert-warning text-center" role="alert">
                    Nenhuma pergunta foi carregada. Por favor, 
                    <a href="/quiz/upload/" class="alert-link">faça o upload de um arquivo de quiz</a>.
                </div>`;
        }
        return;
    }

    // Handler para cliques nas alternativas
    document.querySelector('.choices')?.addEventListener('click', async function(event) {
        if (!event.target.classList.contains('choice-btn')) return;
        
        const choiceButton = event.target;
        const selectedAnswer = choiceButton.dataset.answer;
        const currentQuestionIndex = elements.questionBlock.dataset.questionIndex;

        // Desabilita todos os botões após a escolha
        document.querySelectorAll('.choice-btn').forEach(btn => btn.disabled = true);

        try {
            const response = await fetch('/quiz/submit_answer/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `question_index=${currentQuestionIndex}&answer=${encodeURIComponent(selectedAnswer)}`
            });
            
            const data = await response.json();
            
            // Atualiza a interface com o resultado
            if (data.correct) {
                choiceButton.classList.add('correct');
                elements.feedbackArea.style.backgroundColor = 'var(--soft-success)';
                quizState.score++;
                quizState.answeredCorrectlyCount++;
                elements.currentScoreEl.textContent = quizState.score;
            } else {
                choiceButton.classList.add('incorrect');
                document.querySelectorAll('.choices .choice-btn').forEach(btn => {
                    if (btn.dataset.answer === data.correct_answer) {
                        btn.classList.add('correct');
                    }
                });
                elements.feedbackArea.classList.add('alert-danger');
            }

            elements.answeredCountEl.textContent = (parseInt(elements.answeredCountEl.textContent || '0') + 1).toString();
            elements.feedbackArea.textContent = data.feedback_message;
            elements.feedbackArea.style.display = 'block';

            if (data.next_question) {
                quizState.nextQuestionData = data.next_question;
                elements.nextQuestionBtn.style.display = 'block';
            } else if (data.quiz_finished) {
                document.getElementById('final-score').textContent = data.score.toString();
                document.getElementById('total-q-final').textContent = data.total_questions.toString();
                document.getElementById('final-errors').textContent = (data.total_questions - data.score).toString();
                
                elements.questionBlock.style.display = 'none';
                elements.feedbackArea.style.display = 'none';
                elements.nextQuestionBtn.style.display = 'none';
                
                // Mostra o card de resultados
                if (elements.quizFinishedMessage) {
                    elements.quizFinishedMessage.style.display = 'block';
                    elements.quizFinishedMessage.classList.add('show');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            elements.feedbackArea.textContent = 'Erro ao processar resposta. Tente novamente.';
            elements.feedbackArea.style.backgroundColor = 'var(--soft-danger)';
            elements.feedbackArea.style.display = 'block';
            document.querySelectorAll('.choice-btn').forEach(btn => btn.disabled = false);
        }
    });

    // Handler para o botão de próxima questão
    elements.nextQuestionBtn?.addEventListener('click', function() {
        if (!quizState.nextQuestionData) return;

        elements.questionBlock.dataset.questionIndex = quizState.nextQuestionData.index;
        document.querySelector('.question-text').textContent = quizState.nextQuestionData.text;

        const choicesContainer = document.querySelector('.choices');
        choicesContainer.innerHTML = quizState.nextQuestionData.choices
            .map(choice => `
                <button class="choice-btn btn btn-outline-primary" data-answer="${choice.text}">
                    ${choice.text}
                </button>
            `).join('');

        elements.feedbackArea.style.display = 'none';
        elements.feedbackArea.style.backgroundColor = '';
        elements.nextQuestionBtn.style.display = 'none';

        document.querySelectorAll('.choices .choice-btn').forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('correct', 'incorrect');
        });
    });
});
