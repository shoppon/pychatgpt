"""OpenAI client
"""
import openai

from pychatgpt.models.chatgpt import Conversation


class OpenAIClient:
    """A client for OpenAI
    """

    def __init__(self, api_key, proxy=None, timeout=60) -> None:
        openai.api_key = api_key
        openai.proxy = proxy
        self.timeout = timeout

    def ask(self, prompt: str, conversation: Conversation) -> str:
        """Ask a question
        """
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation.messages + [
                {"role": "user", "content": prompt}
            ],
            timeout=self.timeout,
        )
        return completion.choices[0].message.content.strip()
