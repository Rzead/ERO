import re
import os

def extract_balanced(text, start_pattern):
    idx = text.find(start_pattern)
    if idx == -1:
        return None, -1, -1
    
    start_idx = idx + len(start_pattern)
    brace_count = 1
    current_idx = start_idx
    while current_idx < len(text) and brace_count > 0:
        char = text[current_idx]
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        current_idx += 1
        
    if brace_count == 0:
        return text[start_idx : current_idx - 1], idx, current_idx
    return None, -1, -1

def replace_command(text, command_name, replace_func):
    pattern = '\\' + command_name + '{'
    while True:
        content, start_idx, end_idx = extract_balanced(text, pattern)
        if content is None:
            break
        replacement = replace_func(content)
        text = text[:start_idx] + replacement + text[end_idx:]
    return text

def clean_text(txt):
    txt = txt.replace('{,}', ',')
    txt = txt.replace('~', ' ')
    txt = txt.replace('\\,', ' ')
    txt = txt.replace('\\$', '$')
    txt = txt.replace('\\%', '%')
    txt = txt.replace(r'\noindent', '')
    txt = txt.replace(r'\centering', '')
    txt = txt.replace(r'\hfill', ' ')
    txt = txt.replace(r'\small', '')
    txt = txt.replace('``', '"').replace("''", '"')
    txt = re.sub(r'\\cite\{([^}]+)\}', r'[\1]', txt)
    txt = re.sub(r'\\ref\{([^}]+)\}', r'[\1]', txt)
    txt = re.sub(r'\\label\{([^}]+)\}', '', txt)
    return txt

def parse_tabular_to_md(tabular_str):
    # Find matching brace of tabular layout parameter
    start_tabular = tabular_str.find(r'\begin{tabular}')
    if start_tabular == -1:
        return ""
    start_brace = tabular_str.find('{', start_tabular + len(r'\begin{tabular}'))
    if start_brace == -1:
        return ""
    
    brace_count = 1
    idx = start_brace + 1
    while idx < len(tabular_str) and brace_count > 0:
        if tabular_str[idx] == '{':
            brace_count += 1
        elif tabular_str[idx] == '}':
            brace_count -= 1
        idx += 1
    if brace_count > 0:
        return ""
        
    end_tabular_idx = tabular_str.find(r'\end{tabular}')
    if end_tabular_idx == -1:
        return ""
        
    tabular_body = tabular_str[idx : end_tabular_idx].strip()
    
    # Remove toprule, midrule, bottomrule, hline before splitting
    for cmd in [r'\toprule', r'\midrule', r'\bottomrule', r'\hline']:
        tabular_body = tabular_body.replace(cmd, '')
    
    rows = []
    for line in tabular_body.split(r'\\'):
        line = line.strip()
        if not line:
            continue
        # Split cells by &
        cells = [clean_text(cell.strip()) for cell in line.split('&')]
        # apply styles
        cleaned_cells = []
        for cell in cells:
            cell = replace_command(cell, 'textbf', lambda x: f"**{x}**")
            cell = replace_command(cell, 'emph', lambda x: f"*{x}*")
            cell = replace_command(cell, 'texttt', lambda x: f"`{x}`")
            cleaned_cells.append(cell)
        rows.append(cleaned_cells)
        
    if not rows:
        return ""
        
    num_cols = max(len(r) for r in rows)
    for i in range(len(rows)):
        while len(rows[i]) < num_cols:
            rows[i].append("")
            
    md_table = []
    # Header row
    md_table.append("| " + " | ".join(rows[0]) + " |")
    # Separator row
    md_table.append("| " + " | ".join(["---"] * num_cols) + " |")
    # Data rows
    for row in rows[1:]:
        md_table.append("| " + " | ".join(row) + " |")
        
    return "\n" + "\n".join(md_table) + "\n"

def convert_latex_to_md(tex_content):
    # Remove comment lines and inline comments
    content = ""
    for line in tex_content.splitlines():
        stripped = line.strip()
        if stripped.startswith('%'):
            continue
        new_line = ""
        escaped = False
        for char in line:
            if char == '\\' and not escaped:
                escaped = True
                new_line += char
            elif char == '%' and not escaped:
                break
            else:
                escaped = False
                new_line += char
        content += new_line + "\n"

    # Extract title, author, date with balanced braces
    title, _, _ = extract_balanced(content, r'\title{')
    author, _, _ = extract_balanced(content, r'\author{')
    date, _, _ = extract_balanced(content, r'\date{')
    
    md_header = []
    if title:
        title_clean = clean_text(title)
        title_clean = replace_command(title_clean, 'textbf', lambda x: f"{x}")
        title_clean = re.sub(r'\\vspace\{[^}]*\}', '', title_clean).strip()
        md_header.append(f"# {title_clean}\n")
    if author:
        author_clean = clean_text(author)
        md_header.append(f"**Auteurs :** {author_clean}\n")
    if date:
        date_clean = clean_text(date)
        date_clean = re.sub(r'\\vspace\{[^}]*\}', '', date_clean).strip()
        if date_clean:
            md_header.append(f"**Date :** {date_clean}\n")
            
    # Extract abstract
    abstract_start = content.find(r'\begin{abstract}')
    if abstract_start != -1:
        abstract_end = content.find(r'\end{abstract}', abstract_start)
        if abstract_end != -1:
            abstract = content[abstract_start + len(r'\begin{abstract}'):abstract_end].strip()
            # Clean abstract
            abstract = clean_text(abstract)
            abstract = replace_command(abstract, 'emph', lambda x: f"*{x}*")
            abstract = replace_command(abstract, 'textbf', lambda x: f"**{x}**")
            abstract = replace_command(abstract, 'texttt', lambda x: f"`{x}`")
            
            abstract_lines = "\n> ".join(abstract.split('\n'))
            md_header.append(f"> **Résumé**\n> {abstract_lines}\n")
        
    # Find start of body
    doc_start = content.find(r'\begin{document}')
    if doc_start != -1:
        body = content[doc_start + len(r'\begin{document}'):]
    else:
        body = content
        
    body = re.sub(r'\\end\{document\}', '', body)
    body = re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}', '', body, flags=re.DOTALL)
    body = re.sub(r'\\maketitle', '', body)
    
    # Process tables first
    while True:
        table_start = body.find(r'\begin{table}')
        if table_start == -1:
            break
        table_end = body.find(r'\end{table}', table_start)
        if table_end == -1:
            break
        
        table_block = body[table_start : table_end + len(r'\end{table}')]
        
        # Extract caption
        caption, _, _ = extract_balanced(table_block, r'\caption{')
        
        # Extract tabular
        tabular_md = ""
        tabular_start = table_block.find(r'\begin{tabular}')
        if tabular_start != -1:
            tabular_end = table_block.find(r'\end{tabular}', tabular_start)
            if tabular_end != -1:
                tabular_content = table_block[tabular_start : tabular_end + len(r'\end{tabular}')]
                tabular_md = parse_tabular_to_md(tabular_content)
                
        replacement = tabular_md
        if caption:
            caption_clean = clean_text(caption)
            caption_clean = replace_command(caption_clean, 'textbf', lambda x: f"**{x}**")
            caption_clean = replace_command(caption_clean, 'emph', lambda x: f"*{x}*")
            replacement += f"\n\n*Table : {caption_clean}*\n"
            
        body = body[:table_start] + replacement + body[table_end + len(r'\end{table}'):]

    # Process figures
    while True:
        fig_start = body.find(r'\begin{figure}')
        if fig_start == -1:
            break
        fig_end = body.find(r'\end{figure}', fig_start)
        if fig_end == -1:
            break
            
        fig_block = body[fig_start : fig_end + len(r'\end{figure}')]
        
        caption, _, _ = extract_balanced(fig_block, r'\caption{')
        imgs = re.findall(r'\\includegraphics\[?[^]]*\]?\{([^}]+)\}', fig_block)
        
        md_imgs = []
        caption_clean = clean_text(caption) if caption else ""
        caption_clean = replace_command(caption_clean, 'textbf', lambda x: f"**{x}**")
        caption_clean = replace_command(caption_clean, 'emph', lambda x: f"*{x}*")
        
        for img in imgs:
            md_imgs.append(f"![{caption_clean}]({img})")
            
        replacement = "\n".join(md_imgs)
        if caption_clean:
            replacement += f"\n\n*Figure : {caption_clean}*\n"
            
        body = body[:fig_start] + replacement + body[fig_end + len(r'\end{figure}'):]

    # Process bibliography
    bib_start = body.find(r'\begin{thebibliography}')
    if bib_start != -1:
        bib_end = body.find(r'\end{thebibliography}', bib_start)
        if bib_end != -1:
            bib_content = body[bib_start + len(r'\begin{thebibliography}'):bib_end].strip()
            # remove the label format like {9}
            if bib_content.startswith('{'):
                # find matching }
                brace_count = 1
                idx = 1
                while idx < len(bib_content) and brace_count > 0:
                    if bib_content[idx] == '{':
                        brace_count += 1
                    elif bib_content[idx] == '}':
                        brace_count -= 1
                    idx += 1
                if brace_count == 0:
                    bib_content = bib_content[idx:].strip()
            
            bib_content = bib_content.replace(r'\small', '')
            
            items = []
            parts = bib_content.split(r'\bibitem')
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                item_match = re.match(r'\{([^}]+)\}\s*(.*)', part, re.DOTALL)
                if item_match:
                    key = item_match.group(1)
                    text = item_match.group(2).strip()
                    text = clean_text(text)
                    text = replace_command(text, 'emph', lambda x: f"*{x}*")
                    text = replace_command(text, 'textbf', lambda x: f"**{x}**")
                    items.append(f"- **[{key}]** {text}")
            
            bib_md = "\n## Références\n\n" + "\n".join(items) + "\n"
            body = body[:bib_start] + bib_md + body[bib_end + len(r'\end{thebibliography}'):]

    # Sections
    body = replace_command(body, 'section', lambda x: f"\n# {x}\n")
    body = replace_command(body, 'subsection', lambda x: f"\n## {x}\n")
    body = replace_command(body, 'subsubsection', lambda x: f"\n### {x}\n")
    body = replace_command(body, 'paragraph', lambda x: f"\n**{x}**\n")
    
    # Lists
    body = body.replace(r'\begin{itemize}', '')
    body = body.replace(r'\end{itemize}', '')
    body = body.replace(r'\begin{enumerate}', '')
    body = body.replace(r'\end{enumerate}', '')
    body = re.sub(r'\\item\s*', r'\n- ', body)
    
    # Text styles
    body = replace_command(body, 'textbf', lambda x: f"**{x}**")
    body = replace_command(body, 'emph', lambda x: f"*{x}*")
    body = replace_command(body, 'texttt', lambda x: f"`{x}`")
    
    # Clean text rules
    body = clean_text(body)
    
    # Equations
    body = re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}', r'\n$$\1$$\n', body, flags=re.DOTALL)
    
    # Clean remaining double vspace or similar tags
    body = re.sub(r'\\vspace\{[^}]*\}', '', body)
    
    final_md = "\n".join(md_header) + "\n" + body
    final_md = re.sub(r'\n{3,}', '\n\n', final_md)
    lines = [line.lstrip() if not line.startswith(' ') else line for line in final_md.splitlines()]
    final_md = "\n".join(lines)
    
    return final_md

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tex_path = os.path.join(script_dir, 'main.tex')
    md_path = os.path.join(script_dir, 'main.md')
    
    with open(tex_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()
        
    md_content = convert_latex_to_md(tex_content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Successfully converted {tex_path} to {md_path}")
