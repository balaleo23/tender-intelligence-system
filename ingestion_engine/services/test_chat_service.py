from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(
    model='mistral',
    messages=[
        {
            'role': 'user',
            'content': 'Why is the sky blue?',
        },
    ],
)

print(response['message']['content'])
print(response.message.content)

# payload = {
#     "model": "llama3",
#     "messages": [
#         {"role": "user", "content": "What is a tender?"}
#     ],
#     "stream": False
# }

# response = requests.post(
#     "http://localhost:11434/api/chat",
#     json=payload,
#     timeout=120
# )

# print(response.status_code)
# print(response.json()["message"]["content"])