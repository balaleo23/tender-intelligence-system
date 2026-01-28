from ingestion_engine.chatbot import ask_chatbot_structured

def ask_chatbot():
    while True:
        question = input("Ask a tender-related question (or 'exit'): ")
        if question.lower() == 'exit':
            break
            
        try:
            # Use structured version:
            result = ask_chatbot_structured(question)
            answer = result['answer']
            citations = result['citations']
            
            print(f"\nAnswer: {answer}")
            print(f"Citations: {citations}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    ask_chatbot()