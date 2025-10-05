def generate_quiz_prompt(commands_text: str) -> str:
    """
    Generate a quiz prompt based on the user's command history.
    
    Args:
        commands_text (str): The text containing user's past commands and responses.
    
    Returns:
        str: The generated quiz prompt.
    """
    prompt = "You are a quiz generator. "
    prompt += "Generate exactly 3 DIFFERENT questions based on the following commands and responses. "
    prompt += "The questions should test the user on their knowledge of previously asked questions and similar concepts. "
    prompt += "Make the questions increase in difficulty. "
    prompt += "The expected responses to the questions are to be a single phrase terminal command, so ask appropriate questions. "
    prompt += "Return ONLY the 3 questions, one per line, numbered as 1., 2., and 3. "
    prompt += "Do NOT include any greetings, formalities, or extra text. Just the 3 numbered questions.\n"
    prompt += f"\nHere are the commands and responses history from the user:\n{commands_text}\n"
    
    return prompt

def evaluate_correctness(question: str, user_answer: str) -> str:
    """
    Evaluate the correctness of the user's answer.
    
    Args:
        question (str): The question that was asked.
        user_answer (str): The user's answer to evaluate.
    
    Returns:
        str: Feedback on the correctness of the answer.
    """
    eval_prompt = "You are an expert at evaluating answers to questions about terminal commands.\n\n"
    eval_prompt += f"Question: {question}\n"
    eval_prompt += f"User's Answer: {user_answer}\n\n"
    eval_prompt += "Evaluate the answer for correctness and provide constructive feedback.\n\n"
    eval_prompt += "Format your response as follows:\n"
    eval_prompt += "- If CORRECT: Start with 'Correct!' and optionally add a brief encouraging note.\n"
    eval_prompt += "- If INCORRECT: Start with 'Incorrect.' Then on a new line, explain why it's wrong and provide the correct answer.\n\n"
    eval_prompt += "Keep your feedback concise, clear, and well-formatted with proper line breaks for readability."
    
    return eval_prompt