import os
import openai
from datetime import datetime

class DigestSummarizer:
    def __init__(self, 
        model: str = "gpt-4o-mini", 
        prompt: str = "", 
        temperature: float = 0.2, 
        api_key: str = "", 
        max_tokens: int = 2000, 
        max_retries: int = 3):

        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        openai.api_key = self.api_key

    def summarize_posts(self, posts):
        summaries = []
        for post in posts:
            summary = self._summarize_post_with_retries(post)
            summaries.append(summary)
        return summaries

    def _summarize_post_with_retries(self, post):
        for attempt in range(self.max_retries):
            try:
                return self._summarize_post(post)
            except openai.error.OpenAIError as e:
                if attempt == self.max_retries - 1:
                    raise e

    def _summarize_post(self, post):
        prompt = f"{self.prompt}\n\nPost Title: {post.title}\n Post Content:\n{post.content}"
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        summary = response.choices[0].message['content'].strip()
        return summary
