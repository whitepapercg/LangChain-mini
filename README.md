# 🦜️🔗 LangChain-mini 
This is a **python** re-implementation of [LangChain-mini](https://github.com/ColinEberhardt/langchain-mini/), in ~150 lines of code. In essence, it is an LLM (GPT-3.5) powered chat application that is able to use tools (Google search and a calculator) in order to hold conversations and answer questions. 

**Here's an example of using search tool:**

~~~
user: Who won the 2022 World Cup?
assistant[Search]: The winner of the 2022 World Cup was the Argentina national football team.
user: Who has scored the most goals and how many in this championship?
assistant[Search]**: The player who scored the most goals in the 2022 World Cup was Kylian Mbappé with a total of 8 goals.
user: How many goals have scored in this championship not counting his goals?
~~~

**An example of simple math calculation and sequential tool usage:**

~~~
user: Help me solve the equation x=(12*34)*56/78/9
assistant[Calculator]: x ≈ 32.547008547008545
user: Solve the three equations: x=11.11*12.12, y=13.13*14.14, z=15.15*16.16
assistant[Calculator][Calculator][Calculator]:
x = 134.6532
y = 185.65820000000002
z = 244.824
~~~

**Expert tool, an attempt to use the [Skeleton-of-Thought](https://arxiv.org/pdf/2307.15337.pdf) idea:**

~~~
user: Use expert to write python code that outputs the current time as words

[TOOL] Expert Query: Python code to output current time as words
[TOOL] Expert Skeleton:
1. Import the necessary modules.
2. Get the current time.
3. Convert the current time to words.
4. Print the current time in words.
[TOOL] Expert Response:
1. To begin, we need to import the necessary modules in order to work with time and convert it to words. This can be done using the `datetime` module in Python.
2. Next, we can use the `datetime.now()` function to get the current time.
3. To convert the current time to words, we can define a function that takes the hour and minute values and returns the corresponding words. We can use a combination of if-else statements and dictionaries to map the numbers to words.
4. Finally, we can print the current time in words using the function we defined in step 3. We can pass the hour and minute values obtained in step 2 to this function and display the result.
In conclusion, by following these steps, we can write a Python code that outputs the current time as words.

assistant[Expert]: Here is the Python code to output the current time as words:
```python
from datetime import datetime
def time_to_words(hour, minute):
    # Define dictionaries for mapping numbers to words
    hours = {
        1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve"
    }
    minutes = {
        0: "o'clock", 1: "one minute", 2: "two minutes", 3: "three minutes", 4: "four minutes", 5: "five minutes",
        6: "six minutes", 7: "seven minutes", 8: "eight minutes", 9: "nine minutes", 10: "ten minutes",
        11: "eleven minutes", 12: "twelve minutes", 13: "thirteen minutes", 14: "fourteen minutes",
        15: "quarter", 16: "sixteen minutes", 17: "seventeen minutes", 18: "eighteen minutes",
        19: "nineteen minutes", 20: "twenty minutes", 21: "twenty-one minutes", 22: "twenty-two minutes",
        23: "twenty-three minutes", 24: "twenty-four minutes", 25: "twenty-five minutes", 26: "twenty-six minutes",
        27: "twenty-seven minutes", 28: "twenty-eight minutes", 29: "twenty-nine minutes", 30: "half"
    }
    # Convert hour to words
    if hour > 12:
        hour -= 12
    hour_word = hours.get(hour)
    # Convert minute to words
    minute_word = minutes.get(minute)
    # Construct the time in words
    if minute == 0:
        time_word = f"It's {hour_word} {minute_word}"
    elif minute <= 30:
        time_word = f"It's {minute_word} past {hour_word}"
    else:
        minute_word = minutes.get(60 - minute)
        hour_word = hours.get((hour % 12) + 1)
        time_word = f"It's {minute_word} to {hour_word}"
    return time_word
current_time = datetime.now().time()
hour = current_time.hour
minute = current_time.minute
print(time_to_words(hour, minute))
```
This code will output the current time as words in the format "It's [time] [past/to] [hour]". For example, if the current time is 2:45, it will output "It's quarter to three".
~~~

Algorithm
~~~
Question > LLM (Skeleton creator) > Question + SoT > LLM (Expert)
~~~
Prompt-preparer for Expert tool
~~~
You’re an organizer responsible for only giving the skeleton (not the full content) for answering the question.
Provide the skeleton in a list of points (numbered 1., 2., 3., etc.) to answer the question.
Instead of writing a full sentence, each skeleton point should be very short with only 3∼5 words. Generally, the skeleton should have 3∼10 points.
~~~

## Differences from the original JS-version
- **History Storage**
- **Rejecting the use of MergeHistory** - Replaced with the limiter of tokens for history (default is 4096 tokens)
- **Reworked algorithm for processing model response cycles.**
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