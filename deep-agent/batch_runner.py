import os
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from graph import create_graph
from utils.pdf_generator import generate_pdf
from utils.storage import upload_file

# Load environment variables
load_dotenv()

def generate_daily_topics():
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    system_prompt = """You are a senior technical interviewer planning a daily batch of 5 deep dive interview questions.
    Given the theme "Trending Research and Production Best Practices in Generative AI", generate 5 distinct, specific sub-topics.
    
    Examples:
    - Speculative Decoding for Latency
    - RAG Context Window Tradeoffs
    - KV Cache Optimization
    - LoRA Fine-tuning Stability
    - Agentic Tool Use Patterns
    
    Return only the 5 topics, separated by commas. Do not number them."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Generate 5 topics.")
    ])
    
    chain = prompt | llm | CommaSeparatedListOutputParser()
    return chain.invoke({})

def run_batch():
    print(f"[{datetime.now()}] Starting Daily Batch Run...")
    
    topics = generate_daily_topics()
    print(f"Generated Topics: {topics}")
    
    app = create_graph()
    results = []
    
    for topic in topics:
        print(f"\nProcessing Topic: {topic}")
        initial_state = {
            "topic": topic,
            "iteration": 0,
            "research_queries": [],
            "papers": [],
            "selected_paper": None,
            "generated_question": None,
            "feedback": None,
            "linkedin_post": None
        }
        
        try:
            final_state = app.invoke(initial_state)
            question = final_state.get("generated_question")
            linkedin_post = final_state.get("linkedin_post")
            
            if question:
                # Add topic to question dict for PDF generation
                question["topic"] = topic
                results.append(question)
                
                # Save LinkedIn post
                safe_topic = topic.replace(" ", "_").replace("/", "-")
                post_filename = f"linkedin_post_{safe_topic}.txt"
                with open(post_filename, "w") as f:
                    f.write(linkedin_post or "Failed to generate post.")
                
                # Upload LinkedIn post to S3
                upload_file(post_filename)
                    
        except Exception as e:
            print(f"Error processing topic {topic}: {e}")
            
    # Generate PDF
    if results:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"Daily_Interview_Questions_{date_str}.pdf"
        generate_pdf(results, filename)
        print(f"\nBatch Complete! PDF saved to {filename}")
        
        # Upload PDF to S3
        pdf_url = upload_file(filename)
        if pdf_url:
            print(f"PDF available at: {pdf_url}")
    else:
        print("\nBatch Failed! No questions generated.")

if __name__ == "__main__":
    run_batch()
