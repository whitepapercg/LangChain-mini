import json
import math
import os
import asyncio
import aiohttp
import time
import re as r
from datetime import datetime
from abc import abstractmethod
from typing import List
import httpx
import openai
from sympy import *
from dotenv import load_dotenv
load_dotenv()
from wp_debugger import debug #can be replaced by print()

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
    def history(self) -> List[dict[str, str, int]]: #role, content, tokens length
        return self._history

    @property
    def dict_to_history(self) -> List[dict[str, str]]:
        return [{k: d[k] for k in ['role','content'] if k in d} for d in self._history]
    
    def get_total_tokens(self) -> int:
        return sum(key['tokens'] for key in self.history)

    def add_to_history(self, info: List[dict[str, str, int]]):
        if isinstance(info, dict): self._history.append(info)
        else: raise TypeError('Expected dictionary')

    def trim_history(self):
        sum_tokens = self.get_total_tokens()
        if sum_tokens >= 4096:
            while sum_tokens >= 4096:
                tokens = self._history[0]['tokens']
                sum_tokens -= int(tokens)                
                del self._history[0]
            print(f'[TOOL] History is pruned to {str(sum_tokens)} tokens')

# --------------------- Utils Handlers --------------------- #
class Utils:
    @staticmethod
    def get_value(string, startswith):
        return next((line[len(startswith):] for line in string.split('\n') if line.startswith(startswith)), None)

    def prepare(text):        
        return '\n'.join(line for line in text.split('\n') if line.strip())

    last_request_time = datetime.min
    def timeout(THRESHOLD_SECONDS):               
        time_diff = (datetime.now() - Utils.last_request_time).total_seconds()
        if time_diff < THRESHOLD_SECONDS: time.sleep(THRESHOLD_SECONDS - time_diff)            
        Utils.last_request_time = datetime.now()


class OpenAIUtils:
    @staticmethod
    async def request_openai(prompt:str, historyHook:bool, template:str = '') -> str:
        Utils.timeout(10)
        data = history_manager.dict_to_history if historyHook else []
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
            p_tokens = response.usage.prompt_tokens-319
            data = {
                'p_tokens': p_tokens,
                'c_tokens': response.usage.completion_tokens,
                'content': response.choices[0].message.content
                }
            return data
        except openai.error.APIError as e:
            if hasattr(e, 'response') and 'detail' in e.response: error_message = e.response['detail']
            else: error_message = str(e)
            print(error_message)

# --------------------- AITools Handlers --------------------- #
class Tool:
    description: str
    @abstractmethod
    async def execute(self, input:str):
        pass

class Expert(Tool):
    description = "Useful for answering questions and completing tasks. You're organizer responsible only giving the skeleton (not the full content) for answering the question. Provide to input of this tool a Question with a Skeleton in a list of points (numbered 1, 2, 3, etc.) to answer the question. Instead of writing a full sentence, each skeleton point should be very short, only 3-5 words. Generally, the skeleton should have 3-10 points."
    async def execute(self, input:str) -> str:
        debug(f'[TOOL] Expert: {input}')
        data = await OpenAIUtils.request_openai(input, True, 'Answer the following question as best you can.')
        response = Utils.prepare(data['content'])
        debug(f'[TOOL] Expert Response: {response}')
        return response

class Calculator(Tool):
    description = 'Useful for getting the result of a math expression. Input should be a valid mathematical expression that could be executed by a simple calculator.'
    async def execute(self, input:str) -> str:
        if '=' in input: input = input.split('=')[1]
        parse = str(parse_expr(r.sub(r"[^0-9\-+=/:.,*]", "", input)))
        result = eval(parse)
        debug(f'[TOOL] Calculation: {input} = {result}')
        return result

# SerpAPI Search Engine
class SearchEngine(Tool):
    description = 'a search engine. Useful for when you need to answer questions about current events. Input should be a search query.'
    async def execute(self, input:str) -> str:
        debug(f'[TOOL] Search: {input}')
        params = {'api_key': SERPAPI_KEY,'q': input} 
        async with httpx.AsyncClient() as client: response = await client.get('https://serpapi.com/search', params=params)
        return response.json().get('answer_box', {}).get('answer') or response.json().get('answer_box', {}).get('snippet') or response.json().get('organic_results', [{}])[0].get('snippet')

# # Analog Search Engine
# class SearchEngine(Tool):
#     description = 'a search engine. Useful for when you need to answer questions about current events. input should be a search query.'
#     async def analogSearch(self, input: str) -> str:
#         debug(f'[TOOL] Search: {input}')
#         async with httpx.AsyncClient() as client:
#             response = await client.get('https://ddg-api.herokuapp.com/search', params={'query': input, 'region': 'ru-ru', 'limit': 3})
#         blob = '\n\n'.join([f'[{index+1}] \'{result['snippet']}\'' for index, result in enumerate(response.json())])
#         return blob

# --------------------- Main --------------------- #
class QuestionAssistant:
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
        self.tools = {
            'Expert': Expert(),
            'Calculator': Calculator(),
            'Search': SearchEngine()
        }

    async def complete_prompt(self, prompt: str, historyHook: bool = True) -> str:
        tools_description = '\n'.join([f'{toolname}: {self.tools[toolname].description}' for toolname in self.tools.keys()])
        template = f'Knowledge cutoff: 2021-09-01 Current date: {datetime.now().strftime("%Y-%m-%d")}.\n{promptTemplate.replace("${tools}", tools_description)}'
        response = await OpenAIUtils.request_openai(prompt, historyHook, template)
        return response

    async def answer_question(self, question: str) -> str:
        prompt = f'Question: {question}\nThought:'
        module_history = ''
        while True:
            action = ''                      
            data = await QuestionAssistant.complete_prompt(self, prompt)
            if 'f_iter' not in locals():
                question_tokens = data['p_tokens']       
                f_iter = True
            response = Utils.prepare(data['content'])
            len_response = len(response)
            if 'Action: ' in response:
                action = Utils.get_value(response, 'Action: ')  
                if action in self.tools.keys():
                    actionInput = Utils.get_value(response, 'Action Input: ')      
                    response = response.split('Action Result:')[0]
            if 'Final Answer:' in response:
                result = response.split('Final Answer:')[-1].strip()
                answer_tokens = math.ceil(data['c_tokens'] * (len(result) / len_response))       
                history_manager.add_to_history({'role': 'user','content': question, 'tokens': question_tokens})
                history_manager.add_to_history({'role': 'assistant','content': result, 'tokens': answer_tokens})
                history_manager.trim_history()
                return f'assistant{module_history}: {result}'
            prompt += '\n' + response
            if action in self.tools.keys():
                module_history += f'[{action}]'
                result = await self.tools[action].execute(actionInput)
                prompt += f'\nAction Result: {result}\nThought: '
            prompt = Utils.prepare(prompt)

promptTemplate = open('prompt.txt', 'r').read()
history_manager = HistoryManager()
assistant = QuestionAssistant(history_manager)

while True:
    question = input('user: ')
    answer = asyncio.run(assistant.answer_question(question))    
    print(answer)