import os
import sys
from dotenv import load_dotenv
from graph import create_graph

# Load environment variables
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <topic>")
        sys.exit(1)
        
    topic = sys.argv[1]
    print(f"Starting Deep Agent for topic: {topic}")
    
    app = create_graph()
    
    initial_state = {
        "topic": topic,
        "iteration": 0,
        "research_queries": [],
        "papers": [],
        "selected_paper": None,
        "generated_question": None,
        "feedback": None
    }
    
    for output in app.stream(initial_state):
        for key, value in output.items():
            print(f"Finished node: {key}")
            if key == "reviewer":
                print(f"Feedback: {value.get('feedback')}")
                
    # Final output
    # We need to get the final state. Since stream yields updates, we might need to capture the last state.
    # Alternatively, we can just invoke it.
    
    final_state = app.invoke(initial_state)
    question = final_state.get("generated_question")
    
    if question:
        print("\n=== FINAL INTERVIEW QUESTION ===\n")
        print(f"## {final_state['topic']} Interview Question\n")
        print(f"### The Question\n{question['question']}\n")
        print(f"### Common Wrong Answer\n{question['wrong_answer']}\n")
        print(f"### How It Actually Works\n{question['explanation']}\n")
        print(f"### Key Paper\n{question['citation']}\n")
        
        # Save to file
        filename = f"{topic.replace(' ', '_')}_question.md"
        with open(filename, "w") as f:
            f.write(f"# {final_state['topic']} Interview Question\n\n")
            f.write(f"## The Question\n{question['question']}\n\n")
            f.write(f"## Common Wrong Answer\n{question['wrong_answer']}\n\n")
            f.write(f"## How It Actually Works\n{question['explanation']}\n\n")
            f.write(f"## Key Paper\n{question['citation']}\n")
        print(f"\nSaved to {filename}")
    else:
        print("Failed to generate a question.")

if __name__ == "__main__":
    main()
