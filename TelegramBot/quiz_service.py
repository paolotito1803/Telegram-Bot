import asyncio
import html
import random

import aiohttp
from deep_translator import GoogleTranslator

async def get_questions(category_id):
    # take and translate the questions for a specific category
    url = f"https://opentdb.com/api.php?amount=1&type=multiple&category={category_id}"

    # HTTP request for API
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response: # API request to the link
            data = await response.json() # take the response
            if data['response_code'] != 0: # check if everything is ok
                return None

            row = data['results'][0]

    #translate
    text = [html.unescape(row['question']), html.unescape(row['correct_answer'])] + [html.unescape(x) for x in row['correct_answers']]

    loop = asyncio.get_running_loop()
    tranlator = GoogleTranslator(source='auto', target='it')

    try:
        translated = await loop.run_in_executor(None, lambda : tranlator.translate_batch(text))
    except Exception as e:
        print(f"Translation error {e}")
        return None

    question_text = translated[0]
    correct_answer = translated[1]
    incorrect_answers = translated[2:]

    # mixed option list
    options = incorrect_answers + [correct_answer]
    random.shuffle(options)

    # find the index of the correct one
    correct_index = options.index(correct_answer)

    return {
        text: question_text,
        "options": options,
        "correct_index": correct_index
    }