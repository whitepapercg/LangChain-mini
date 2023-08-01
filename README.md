# 🦜️🔗 LangChain-mini 
This is a **python** re-implementation of [LangChain-mini](https://github.com/ColinEberhardt/langchain-mini/), in ~150 lines of code. In essence, it is an LLM (GPT-3.5) powered chat application that is able to use tools (Google search and a calculator) in order to hold conversations and answer questions. 

Here's an example:

~~~
user: Who won the 2022 World Cup?
assistant[Search]: The winner of the 2022 World Cup was the Argentina national football team.
user: Who has scored the most goals and how many in this championship?
assistant[Search]: The player who scored the most goals in the 2022 World Cup was Kylian Mbappé with a total of 8 goals.
user: How many goals have scored in this championship not counting his goals?
~~~

An example of simple math expression and sequential tool usage.

~~~
user: Help me solve the equation x=(12*34)*56/78/9
assistant[Calculator]: x ≈ 32.547008547008545
user: Solve the three equations: x=11.11*12.12, y=13.13*14.14, z=15.15*16.16
assistant[Calculator][Calculator][Calculator]:
x = 134.6532
y = 185.65820000000002
z = 244.824
~~~

## Differences from the original JS-version
- **Rejecting the use of MergeHistory** - Temporarily replaced by trimming by count of messages. _I will replace it with a more advanced version later._
- **Reworked algorithm for processing model response cycles.**
- **Simple History Storage Manager**
- **Added free analog of search engine** (DuckDuckGo)

## Running / developing

Install dependencies:

~~~
pip install -r requirements.txt
~~~

You'll need to have both an OpenAI and SerpApi keys. These can be supplied to the application via a `.env` file:

~~~
SERPAPI_API_KEY="..."
OPENAI_API_KEY="..."
OPENAI_MODEL="gpt-3.5-turbo"
~~~

You can now run the chain:

~~~
python app.py
How can I help? what was the name of the first man on the moon?
Neil Armstrong
~~~
