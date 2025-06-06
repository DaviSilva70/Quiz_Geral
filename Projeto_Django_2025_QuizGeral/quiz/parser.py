# quiz/parser.py

def parse_quiz_file(file_content):
    """
    Processa um arquivo de texto contendo perguntas e respostas no formato:
    [Texto da pergunta]
    * Alternativa incorreta
    + Alternativa correta
    * Alternativa incorreta
    * Alternativa incorreta

    Retorna uma lista de dicionários com a estrutura:
    {
        "text": "Texto da pergunta",
        "choices": [
            {"text": "Alternativa 1", "is_correct": False},
            {"text": "Alternativa 2", "is_correct": True},
            ...
        ]
    }
    """
    if not file_content or not file_content.strip():
        raise ValueError("Arquivo vazio.")

    questions_data = []
    current_question = None
    current_choices = []
    
    lines = [line.strip() for line in file_content.splitlines()]
    
    for line in lines:
        if not line:  # Pula linhas vazias
            continue
            
        # Se a linha começa com * ou +, é uma alternativa
        if line.startswith('*') or line.startswith('+'):
            if not current_question:
                raise ValueError("Encontrada alternativa sem pergunta associada.")
                
            is_correct = line.startswith('+')
            text = line[1:].strip()
            
            if not text:
                raise ValueError(f"Alternativa vazia encontrada para a pergunta: {current_question}")
                
            current_choices.append({
                "text": text,
                "is_correct": is_correct
            })
        else:
            # Se temos uma questão completa anterior, salvamos ela
            if current_question and current_choices:
                if not any(choice["is_correct"] for choice in current_choices):
                    raise ValueError(f"A pergunta '{current_question}' não tem alternativa correta marcada com '+'")
                    
                questions_data.append({
                    "text": current_question,
                    "choices": current_choices
                })
                current_choices = []
            
            # A linha atual é uma nova pergunta
            current_question = line

    # Não esquecer da última pergunta
    if current_question and current_choices:
        if not any(choice["is_correct"] for choice in current_choices):
            raise ValueError(f"A pergunta '{current_question}' não tem alternativa correta marcada com '+'")
            
        questions_data.append({
            "text": current_question,
            "choices": current_choices
        })
    
    if not questions_data:
        raise ValueError("Nenhuma pergunta válida encontrada no arquivo.")
        
    return questions_data
