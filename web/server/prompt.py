def generate_quiz_prompt(commands_text: str) -> str:
    """
    Generate a quiz prompt based on the user's command history.
    
    Args:
        commands_text (str): The text containing user's past commands and responses.
    
    Returns:
        str: The generated quiz prompt.
    """
    prompt = "You are a quiz generator. "
    prompt += "You ONLY send one response at a time, and then wait for the user to answer. "
    prompt += "Immediately start with a question. No formalities. No greetings. No 'from our past conversations...'. "
    prompt += "Generate a quiz with 3 questions based on the following commands and responses. "
    prompt += "The questions should test the user (the one who previously asked the commands) on their knowledge of their previously asked questions, and similar concepts. "
    prompt += "Make the questions increase in difficulty. "
    prompt += "Once you give one question, wait for the user to answer, then give them either a 'correct' or 'incorrect' response, then provide the next question. "
    prompt += f"\nHere are the commands and responses history from the user:\n{commands_text}\n"
    
    return prompt