# Resume Refiner

Resume Refiner is a personal project that updates the summary section of a LaTeX-based resume using context-aware text generation from the Eden AI API. The tool extracts the original summary from a user's LaTeX resume, accepts a job description along with optional specialized instructions, and generates a new summary. The updated resume is then compiled into a PDF without altering the original resume file.

## Features

- **User Registration:**  
  Users register by uploading their LaTeX resume file. The original resume is stored safely.

- **Context-Aware Summary Refinement:**  
  The app extracts the current summary from the resume and uses it along with a new job description and any specialized instructions to generate a new, authentic professional summary via the Eden AI API (using GPT-4-turbo).

- **Non-Destructive Updates:**  
  The original resume remains unchanged. Updated LaTeX files and compiled PDFs are saved separately with timestamps.

- **PDF Compilation:**  
  Uses `pdflatex` to compile the updated LaTeX file into a downloadable PDF.
