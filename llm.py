from openai import OpenAI

api_key_openai = "YOUR OPENAI API KEY HERE"
api_key_deepseek = "YOUR DEEPSEEK API KEY HERE"

class LLM:
    supported_models = ["deepseek-chat", 'gpt-4o-mini', 'gpt-4o-2024-08-06', 'gpt-4o', 'claude-3-7-sonnet-20250219']
    model = ''
    temp = 0
    top_p = 1
    def __init__(self, conversation=None):
        self.model = LLM.model
        if self.model == 'gpt-4o':
            self.model = 'gpt-4o-2024-08-06'
        self.temp = LLM.temp
        self.top_p = LLM.top_p
        if conversation:
            self.conversation = conversation
        else:
            self.conversation = []
        assert self.model in self.supported_models, f"Unsupported model: {self.model}"
        if 'gpt' in self.model.lower() or 'claude' in self.model.lower():
            self.client = OpenAI(api_key=api_key_openai) 
        elif 'deepseek' in self.model.lower():
            self.client = OpenAI(api_key=api_key_deepseek, base_url="https://api.deepseek.com")
        else:
            raise ValueError(f"Unknown model: {self.model}")


    def query(self, prompt: str, append: bool = True, n: int=1) -> list[str]:
        if append:
            assert n == 1

        messages = self.conversation + [{'role': 'user', 'content': prompt}]
        response = self.client.chat.completions.create(model=self.model,
            messages=messages, n=n, temperature=self.temp, top_p=self.top_p)
        # print(response)
        role = response.choices[0].message.role
        contents = [c.message.content for c in response.choices]
        if append:
            self.conversation.append({'role': 'user', 'content': prompt})
            self.conversation.append({'role': role, 'content': contents[0]})
        return contents

    def add_user_message(self, message: str):
        self.conversation.append({'role': 'user', 'content': message})

    def add_assistant_message(self, message: str):
        self.conversation.append({'role': 'assistant', 'content': message})


if __name__ == '__main__':
    pass
