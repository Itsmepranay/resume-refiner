import os

USER_PROFILES_DIR = "user_profiles"

def save_latex(username, latex_code):
    user_dir = os.path.join(USER_PROFILES_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, "resume.tex")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

def load_latex(username):
    file_path = os.path.join(USER_PROFILES_DIR, username, "resume.tex")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return None
