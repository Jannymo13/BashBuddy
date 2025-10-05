def generate_quiz_prompt(commands_text: str) -> str:
    """
    Generate a quiz prompt based on the user's command history.
    
    Args:
        commands_text (str): The text containing user's past commands and responses.
    
    Returns:
        str: The generated quiz prompt.
    """
    prompt = "You are a quiz generator. "
    prompt += "Immediately start with a question. No formalities. No greetings. No 'from our past conversations...'. "
    prompt += "Generate a quiz with 3 questions based on the following commands and responses. "
    prompt += "The questions should test the user (the one who previously asked the commands) on their knowledge of their previously asked questions, and similar concepts. "
    prompt += "Make the questions increase in difficulty. "
    prompt += "Once you give one question, wait for the user to answer before giving the next question. "
    prompt += "The expected responses to the questions are to be a single phrase terminal command, so ask appropriate questions. "
    prompt += f"\nHere are the commands and responses history from the user:\n{commands_text}\n"
    
    return prompt

def evaluate_correctness(question: str, user_answer: str) -> str:
    """
    Evaluate the correctness of the user's answer.
    
    Args:
        user_answer (str): The user's answer to evaluate.
    
    Returns:
        str: Feedback on the correctness of the answer.
    """
    eval_prompt = "You are an expert at evaluating answers to questions about terminal commands. "
    eval_prompt += f"Question: {question}\n"
    eval_prompt += f"Evaluate the following answer for correctness and provide constructive feedback:\nAnswer: {user_answer}\n"
    eval_prompt += "If the answer is correct, say 'Correct!'. If incorrect, explain why and provide the correct answer."
    
    return eval_prompt