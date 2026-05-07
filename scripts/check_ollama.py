import ollama
models = ollama.list()
print('Ollama OK:', [m.model for m in models.models])
