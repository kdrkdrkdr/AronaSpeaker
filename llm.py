import os
import time


import openai
openai.api_key = "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"


from bardapi import Bard
os.environ['_BARD_API_KEY']="Vwh-D1pxYkZhpVW4crMbE5b0XryIkIPse4Rl8D6KKU2JsVTGSlX9TP-6N1qmDEMy_vyycg."



def AnswerChatGPT(user_input):
    message_log = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    message_log.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_log,
        max_tokens=3800,
        stop=None,
        temperature=0.7, 
    )
    for choice in response.choices:
        if "text" in choice:
            return choice.text
    resp = response.choices[0].message.content

    message_log.append({"role": "assistant", "content": resp})
    print(f"AI assistant: {resp}")
    return resp


def AnswerBard(user_input):
    while True:
        try:
            bard = Bard()
            resp =  bard.get_answer(user_input)['content']
            print(f"AI assistant: {resp}")
            return resp
        except:
            print("아로나가 답변을 생각할 시간을 조금 더 주세요...:)")
            time.sleep(2)
            
