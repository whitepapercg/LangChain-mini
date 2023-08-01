import os
import asyncio
import time
from datetime import datetime
from abc import abstractmethod
from typing import List
import httpx
import openai
from sympy import *
from dotenv import load_dotenv
load_dotenv()
from wp_debugger import debug

#Add this Keys to your .env
openai.api_key = os.getenv('OPENAI_API_KEY')
if os.getenv('OPENAI_API_BASE'): openai.api_base = os.getenv('OPENAI_API_BASE') #only for azure endpoints
SERPAPI_KEY = os.getenv('SERPAPI_API_KEY') #you can use Analog Search Engine (find below)
OPENAI_MODEL = os.getenv('OPENAI_MODEL')

# --------------------- History Manager --------------------- #
class HistoryManager:
    def __init__(self):
        self._history = []

    @property
    def history(self) -> List[dict[str, str]]:
        return self._history

    def add_to_history(self, info: List[dict[str, str]]):
        if isinstance(info, dict): self._history.append(info)
        else: raise TypeError('Expected dictionary')

    def clear_history(self):
        self._history = []

    def trim_history(self, n: int) -> List[dict[str, str]]:
        return self._history if n >= len(self._history) else self._history[-n:]

# --------------------- Utils Handlers --------------------- #
class Utils:
    @staticmethod
    def get_value(string, startswith):
        return next((line[len(startswith):] for line in string.split('\n') if line.startswith(startswith)), None)

    def prepare(text):        
        return '\n'.join(line for line in text.split('\n') if line.strip())

    def timeout(THRESHOLD_SECONDS):
        LOG_FILE = 'request_data.log'
        last_request_time = datetime.fromisoformat(open(LOG_FILE, 'r').read().strip()) if os.path.exists(LOG_FILE) else datetime.min
        time_diff = (datetime.now() - last_request_time).total_seconds()
        if time_diff < THRESHOLD_SECONDS: time.sleep(THRESHOLD_SECONDS - time_diff)            
        with open(LOG_FILE, 'w') as f: f.write(datetime.now().isoformat())


class OpenAIUtils:
    @staticmethod
    async def request_openai(prompt:str, historyHook:bool, template:str = '') -> str:
        Utils.timeout(10)
        history_manager.trim_history(8)
        data = history_manager.history if historyHook else []
        if template: data.append({'role': 'system', 'content': template})
        data.append({'role': 'user', 'content': prompt})
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=data,
                temperature=0.7,
                stream=False,
                stop=['Observation:']
            )
            model = response.model
            content = response.choices[0].message.content
            return content
        except openai.error.APIError as e:
            if hasattr(e, 'response') and 'detail' in e.response: error_message = e.response['detail']
            else: error_message = str(e)
            return error_message

# --------------------- AITools Handlers --------------------- #
class Tool:
    description: str
    @abstractmethod
    async def execute(self, input:str):
        pass

class Calculator(Tool):
    description = 'Useful for getting the result of a math expression. The input to this tool should be a valid mathematical expression that could be executed by a simple calculator.'
    async def execute(self, input:str) -> str:
        if '=' in input: input = input.split('=')[1].strip()
        result = eval(input)
        debug(result)
        return result

# SerpAPI Search Engine
class SearchEngine(Tool):
    description = 'a search engine. Useful for when you need to answer questions about current events. Input should be a search query.'
    async def execute(self, input:str) -> str:
        params = {'api_key': SERPAPI_KEY,'q': input} 
        async with httpx.AsyncClient() as client: response = await client.get('https://serpapi.com/search', params=params)
        return response.json().get('answer_box', {}).get('answer') or response.json().get('answer_box', {}).get('snippet') or response.json().get('organic_results', [{}])[0].get('snippet')
    
# # Analog Search Engine
# class SearchEngine(Tool):
#     description = 'a search engine. Useful for when you need to answer questions about current events. input should be a search query.'
#     async def analogSearch(self, input: str) -> str:
#         async with httpx.AsyncClient() as client:
#             response = await client.get('https://ddg-api.herokuapp.com/search', params={'query': input, 'region': 'ru-ru', 'limit': 3})
#         blob = '\n\n'.join([f'[{index+1}] \'{result['snippet']}\'' for index, result in enumerate(response.json())])
#         return blob

# --------------------- Main --------------------- #
class QuestionAssistant:
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
        self.tools = {
            'Search': SearchEngine(),
            'Calculator': Calculator()
        }

    async def complete_prompt(self, prompt: str, historyHook: bool = True) -> str:
        current_date = datetime.now().strftime('%Y-%m-%d')
        tools_description = '\n'.join([f'{toolname}: {self.tools[toolname].description}' for toolname in self.tools.keys()])
        template = f'Knowledge cutoff: 2021-09-01 Current date: {current_date}.\n{promptTemplate.replace("${tools}", tools_description)}'
        response = await OpenAIUtils.request_openai(prompt, historyHook, template)
        debug(response)
        return response
    
    async def answer_question(self, question: str) -> str:
        prompt = f'Question: {question}'
        module_history = ''
        while True:
            action = ''
            response = Utils.prepare(await QuestionAssistant.complete_prompt(self, prompt))
            if 'Action: ' in response:        
                action = Utils.get_value(response, 'Action: ')  
                if action in self.tools.keys():                                
                    actionInput = Utils.get_value(response, 'Action Input: ')      
                    response = response.split('Observation:')[0]
            if 'Final Answer:' in response:
                result = response.split('Final Answer:')[-1].strip()
                history_manager.add_to_history({'role': 'assistant','content': result})
                return f'assistant{module_history}: {result}'            
            prompt += '\n' + response
            if action in self.tools.keys():
                module_history += f'[{action}]'
                result = await self.tools[action].execute(actionInput)
                prompt += f'\nObservation: {result}\nThought: '
            prompt = Utils.prepare(prompt)
            debug(prompt)

promptTemplate = open('prompt.txt', 'r').read()
history_manager = HistoryManager()
assistant = QuestionAssistant(history_manager)

while True:
    question = input('user: ')
    history_manager.add_to_history({'role': 'user','content': question})
    answer = asyncio.run(assistant.answer_question(question))    
    print(answer)