import ollama

# stream = ollama.chat(
#     model='llama3.1',
#     messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
#     stream=True,
# )

# for chunk in stream:
#   print(chunk['message']['content'], end='', flush=True)
ollama.pull('llama3.1')
print(ollama.list())