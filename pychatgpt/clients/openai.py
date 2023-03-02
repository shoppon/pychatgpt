"""OpenAI client
"""
import openai


class OpenAIClient:
    """A client for OpenAI
    """

    def __init__(self, api_key) -> None:
        openai.api_key = api_key

    def ask(self, prompt: str, conversation_id=None, parent_id=None) -> str:
        """Ask a question
        """
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return {
            "message": completion.choices[0].message,
            "conversation_id": conversation_id,
            "message_id": parent_id,
        }
