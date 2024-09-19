import ollama
client = ollama.Client()
stream = client.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content': "which is the author of the paper 'Using NIST Special Publications (SP) 800-171r2 and 800-172/800-172A to\n  assess and evaluate the Cybersecurity posture of Information Systems in the\n  Healthcare sector' proposed in 2019"}],
    stream=True,
)

for chunk in stream:
  print(chunk['message']['content'], end='', flush=True)
# ollama.pull('llama3.1')
# print(ollama.list())