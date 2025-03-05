import os
import re
import subprocess
import requests
from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime

app = Flask(__name__)

# Directory paths
USER_PROFILES_DIR = os.path.join(os.getcwd(), "user_profiles")
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Full path to pdflatex.exe (adjust as needed)
PDFLATEX_PATH = r"C:\Users\prana\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"

# Eden AI API Key (replace with your actual key)
EDEN_AI_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzc5NmQ0M2UtN2M0MS00YmZjLTlmMTEtYzVmMTllOGNhODQzIiwidHlwZSI6ImFwaV90b2tlbiJ9.fNbGuzFXtSPih7LNOvRFZAFxqE53f_zkWKEifbAzSs4"


def convert_markdown_to_latex(text):
    """
    Converts basic Markdown formatting to LaTeX.
      - **text** becomes \textbf{text}
      - *text* becomes \emph{text}
    """
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\emph{\1}", text)
    return text


def clean_generated_summary(summary):
    """
    Removes the first line of the generated summary entirely.
    """
    lines = summary.splitlines()
    if len(lines) > 1:
        cleaned = "\n".join(lines[1:])
    else:
        cleaned = summary
    return cleaned.strip()


def extract_original_summary(latex_content):
    """
    Extracts the existing summary text from the LaTeX content.
    Looks for text between \section{Summary} and the next \section (or end-of-file).
    """
    pattern = r"\\section\{Summary\}([\s\S]*?)(?=\\section|$)"
    match = re.search(pattern, latex_content)
    if match:
        return match.group(1).strip()
    return ""


def update_summary(latex_content, new_summary):
    """
    Replaces the content in the Summary section with new_summary.
    Searches for \section{Summary} and replaces all text until the next \section or EOF.
    """
    pattern = r"(\\section\{Summary\})([\s\S]*?)(?=\\section|$)"
    replacement = r"\1\n" + new_summary + "\n"
    updated_content, count = re.subn(pattern, replacement, latex_content, count=1)
    if count == 0:
        updated_content = "\\section{Summary}\n" + new_summary + "\n" + latex_content
    return updated_content


def generate_summary(job_desc, original_summary, specialized_instruction):
    """
    Calls the Eden AI API to generate a concise professional summary based on the job description,
    original summary context, and any specialized instructions.
    """
    url = "https://api.edenai.run/v2/multimodal/chat"
    
    # Create the prompt including the specialized instruction if provided.
    prompt_text = (
        f"Given the current professional summary context:\n"
        f"\"{original_summary}\"\n\n"
        f"and the following job description:\n"
        f"\"{job_desc}\"\n\n"
    )
    if specialized_instruction:
        prompt_text += f"Also consider the following specialized instructions:\n\"{specialized_instruction}\"\n\n"
    
    prompt_text += (
        "Generate a concise, authentic, and detailed professional summary that aligns with the user's experience.dont write any thing else execpt the summary.be creative and feel free to change the wording of the original summary"
    )
    
    payload = {
        "response_as_dict": True,
        "attributes_as_list": False,
        "show_base_64": True,
        "show_original_response": True,
        "temperature": 0.7,
        "max_tokens": 200,
        "providers": ["openai/gpt-4-turbo"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "content": {
                            "text": prompt_text
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {EDEN_AI_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    print("Eden AI API response:", response_json)
    
    generated_summary = response_json.get("openai/gpt-4-turbo", {}).get("generated_text", "")
    latex_summary = convert_markdown_to_latex(generated_summary)
    cleaned_summary = clean_generated_summary(latex_summary)
    print("Cleaned summary to be inserted:", repr(cleaned_summary))
    
    return cleaned_summary


def compile_latex(tex_file, output_dir):
    """
    Compiles the given LaTeX file to PDF using pdflatex.
    The PDF is generated in the specified output directory.
    Returns the absolute path to the generated PDF.
    """
    cmd = [
        PDFLATEX_PATH,
        "-interaction=nonstopmode",
        "-output-directory", os.path.abspath(output_dir),
        os.path.abspath(tex_file)
    ]
    
    print("Running command:", " ".join(cmd))
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    print("pdflatex stdout:\n", stdout)
    print("pdflatex stderr:\n", stderr)
    
    if process.returncode != 0:
        raise RuntimeError(f"LaTeX compilation failed with code {process.returncode}:\n{stderr}")
    
    pdf_file = os.path.join(output_dir, os.path.splitext(os.path.basename(tex_file))[0] + ".pdf")
    if not os.path.exists(pdf_file):
        raise FileNotFoundError("PDF file was not generated.")
    
    return pdf_file


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main page for refining an existing resume.
    User inputs username, job description, and optional specialized instructions.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        job_desc = request.form.get("job_desc", "").strip()
        specialized_instruction = request.form.get("specialized", "").strip()
        if not username or not job_desc:
            return "Username and Job Description are required.", 400
        
        user_dir = os.path.join(USER_PROFILES_DIR, username)
        original_tex_file = os.path.join(user_dir, "resume.tex")
        if not os.path.exists(original_tex_file):
            return "User not found. Please register first.", 400
        
        # Read original LaTeX resume
        with open(original_tex_file, "r", encoding="utf-8") as f:
            original_latex = f.read()
        print("Original LaTeX content (first 300 chars):", repr(original_latex[:300]))
        
        # Extract original summary for context
        original_summary = extract_original_summary(original_latex)
        print("Original summary context:", repr(original_summary))
        
        # Generate new summary using job description, original summary, and specialized instructions
        new_summary = generate_summary(job_desc, original_summary, specialized_instruction)
        
        # Create updated LaTeX content without modifying the original file
        updated_latex = update_summary(original_latex, new_summary)
        print("Updated LaTeX content (first 300 chars):", repr(updated_latex[:300]))
        
        # Save the updated LaTeX file in the output folder with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_user_dir = os.path.join(OUTPUT_DIR, username)
        os.makedirs(output_user_dir, exist_ok=True)
        updated_tex_file = os.path.join(output_user_dir, f"{username}_updated_{timestamp}.tex")
        
        with open(updated_tex_file, "w", encoding="utf-8") as f:
            f.write(updated_latex)
        
        try:
            pdf_path = compile_latex(updated_tex_file, output_user_dir)
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            return f"Compilation Error: {e}", 500
    
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration page for new users.
    Users can register by providing a username and uploading their resume (LaTeX file).
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        resume_file = request.files.get("resume")
        if not username or not resume_file:
            return "Username and resume file are required.", 400
        
        user_dir = os.path.join(USER_PROFILES_DIR, username)
        os.makedirs(user_dir, exist_ok=True)
        original_tex_file = os.path.join(user_dir, "resume.tex")
        
        resume_file.save(original_tex_file)
        return redirect(url_for("index"))
    
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
