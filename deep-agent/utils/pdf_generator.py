import markdown
from weasyprint import HTML
import os

def generate_pdf(questions, filename="interview_questions.pdf"):
    """
    Compiles a list of interview questions (dicts) into a single PDF.
    Each question dict should have: topic, question, wrong_answer, explanation, citation.
    """
    
    css = """
    @page { size: A4; margin: 2cm; }
    body { font-family: sans-serif; line-height: 1.6; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
    h2 { color: #2980b9; margin-top: 30px; }
    .question-block { margin-bottom: 40px; page-break-inside: avoid; }
    .section-title { font-weight: bold; color: #7f8c8d; text-transform: uppercase; font-size: 0.9em; margin-top: 15px; }
    .content { margin-top: 5px; }
    .citation { font-style: italic; color: #7f8c8d; font-size: 0.9em; margin-top: 10px; border-top: 1px solid #eee; padding-top: 5px; }
    """
    
    html_content = """
    <html>
    <head></head>
    <body>
    <h1>Daily GenAI Interview Questions</h1>
    """
    
    for i, q in enumerate(questions, 1):
        # Handle cases where keys might be missing or named differently
        topic = q.get("topic", f"Question {i}")
        question_text = q.get("question", "")
        wrong_answer = q.get("wrong_answer", "")
        explanation = q.get("explanation", "")
        citation = q.get("citation", "")
        
        # Convert markdown to HTML for the content fields
        q_html = markdown.markdown(question_text)
        w_html = markdown.markdown(wrong_answer)
        e_html = markdown.markdown(explanation)
        
        block = f"""
        <div class="question-block">
            <h2>{i}. {topic}</h2>
            
            <div class="section-title">The Question</div>
            <div class="content">{q_html}</div>
            
            <div class="section-title">Common Wrong Answer</div>
            <div class="content">{w_html}</div>
            
            <div class="section-title">How It Actually Works</div>
            <div class="content">{e_html}</div>
            
            <div class="citation">Key Paper: {citation}</div>
        </div>
        <hr/>
        """
        html_content += block
        
    html_content += """
    </body>
    </html>
    """
    
    html = HTML(string=html_content)
    css_obj = import_css(css)
    html.write_pdf(filename, stylesheets=[css_obj])
    return filename

def import_css(css_string):
    from weasyprint import CSS
    return CSS(string=css_string)
