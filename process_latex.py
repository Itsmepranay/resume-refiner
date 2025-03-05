import re

def modify_latex_summary(latex_code, new_summary):
    summary_pattern = r"\\section\{Summary\}([\s\S]*?)\\section"
    
    def replacement(match):
        return f"\\section{{Summary}}\n{new_summary}\n\\section"

    updated_latex = re.sub(summary_pattern, replacement, latex_code, count=1)
    return updated_latex
