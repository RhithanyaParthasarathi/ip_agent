import re

def is_greeting_test(question):
    cleaned = re.sub(r'[^\w\s]', '', question.lower()).strip()
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon",
                "good evening", "sup", "howdy", "what's up", "whats up",
                "who are you", "what are you", "what can you do", "help",
                "how are you", "hows it going", "how's it going",
                "hows work", "how was your day", "hi there", "hello there",
                "greet", "morning", "evening"}
    
    words = cleaned.split()
    is_greeting = (
        cleaned in greetings 
        or (words and words[0] in greetings)
    )
    return (f"Question: '{question}' -> Cleaned: '{cleaned}' -> Words: {words} -> Is Greeting: {is_greeting}")

test_cases = ["Hi!", "Hello", "hi", "how are you?", "Who are you", "From Documents"]
with open("test_results.txt", "w") as f:
    for q in test_cases:
        f.write(is_greeting_test(q) + "\n")
