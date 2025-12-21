import os
import glob
import html

# Configuration
SOURCE_DIR = r"d:\D.P. Projesi\Walkthrough_Archives"
GUIDE_FILE = r"d:\D.P. Projesi\Resources_and_Constraints_Location_Guide.md"
OUTPUT_FILE = r"d:\D.P. Projesi\Project_Documentation.html"

CSS = """
<style>
    :root { --primary: #2563eb; --sidebar-width: 300px; --bg: #f8fafc; --text: #334155; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; display: flex; height: 100vh; background: var(--bg); color: var(--text); }
    #sidebar { width: var(--sidebar-width); background: white; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; flex-shrink: 0; }
    #sidebar-header { padding: 20px; border-bottom: 1px solid #e2e8f0; font-weight: bold; font-size: 1.2rem; color: var(--primary); }
    #nav { overflow-y: auto; flex: 1; padding: 10px; }
    .nav-item { display: block; padding: 10px 15px; margin-bottom: 5px; border-radius: 6px; cursor: pointer; color: #64748b; transition: all 0.2s; text-decoration: none; }
    .nav-item:hover { background: #f1f5f9; color: var(--text); }
    .nav-item.active { background: #eff6ff; color: var(--primary); font-weight: 600; }
    #content { flex: 1; overflow-y: auto; padding: 40px; scroll-behavior: smooth; }
    .doc-section { background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 40px; margin-bottom: 40px; max-width: 900px; margin-left: auto; margin-right: auto; display: none; }
    .doc-section.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    h1 { color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 0; }
    h2 { color: #334155; margin-top: 2em; }
    h3 { color: #475569; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; color: #d63384; font-size: 0.9em; }
    pre { background: #1e293b; color: #f8fafc; padding: 20px; border-radius: 8px; overflow-x: auto; }
    pre code { background: transparent; color: inherit; padding: 0; }
    ul { padding-left: 20px; }
    li { margin-bottom: 8px; line-height: 1.6; }
    .timestamp { font-size: 0.85em; color: #64748b; border-left: 3px solid var(--primary); padding-left: 10px; margin: 20px 0; background: #f8fafc; padding: 10px; border-radius: 0 4px 4px 0; }
</style>
"""

SCRIPT = """
<script>
    function showSection(id) {
        document.querySelectorAll('.doc-section').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        document.getElementById('doc-'+id).classList.add('active');
        document.getElementById('nav-'+id).classList.add('active');
    }
</script>
"""

def simple_md_to_html(text):
    html_out = ""
    in_code_block = False
    
    for line in text.split('\n'):
        # Code Blocks
        if line.strip().startswith("```"):
            if in_code_block:
                html_out += "</code></pre>\n"
            else:
                html_out += "<pre><code>"
            in_code_block = not in_code_block
            continue
            
        if in_code_block:
            html_out += html.escape(line) + "\n"
            continue
            
        # Headers
        stripped = line.strip()
        if stripped.startswith("# "):
            html_out += f"<h1>{html.escape(stripped[2:])}</h1>\n"
        elif stripped.startswith("## "):
            html_out += f"<h2>{html.escape(stripped[3:])}</h2>\n"
        elif stripped.startswith("### "):
            html_out += f"<h3>{html.escape(stripped[4:])}</h3>\n"
        # Lists
        elif stripped.startswith("- "):
            html_out += f"<li>{html.escape(stripped[2:])}</li>\n"
        # Metadata
        elif stripped.startswith("Date:") or stripped.startswith("Time of Work:"):
             html_out += f"<div class='timestamp'>{html.escape(stripped)}</div>\n"
        # Empty lines
        elif not stripped:
            html_out += "<br>\n"
        else:
            # simple bold logic
            line_html = html.escape(line)
            # very basic bold parser
            parts = line_html.split("**")
            new_line = ""
            for i, part in enumerate(parts):
                if i % 2 == 1: new_line += f"<b>{part}</b>"
                else: new_line += part
            html_out += f"<p>{new_line}</p>\n"
            
    return html_out

def generate():
    files = []
    
    # 1. Guide File
    if os.path.exists(GUIDE_FILE):
        files.append({
            'id': 'guide',
            'title': '📚 Resource Guide',
            'path': GUIDE_FILE
        })
        
    # 2. Walkthroughs
    archives = glob.glob(os.path.join(SOURCE_DIR, "*.txt"))
    archives.sort(reverse=True) # Newest first
    
    for i, fpath in enumerate(archives):
        fname = os.path.basename(fpath)
        title = fname.replace('.txt', '').replace('_', ' ')
        files.append({
            'id': f'walkthrough_{i}',
            'title': f'🛠️ {title}',
            'path': fpath
        })
        
    # HTML Calc
    nav_html = ""
    content_html = ""
    
    for i, f in enumerate(files):
        with open(f['path'], 'r', encoding='utf-8') as read_file:
            raw = read_file.read()
            
        is_active = "active" if i == 0 else ""
        
        nav_html += f"""
        <a id="nav-{f['id']}" class="nav-item {is_active}" onclick="showSection('{f['id']}')">
            {f['title']}
        </a>
        """
        
        converted = simple_md_to_html(raw)
        
        content_html += f"""
        <div id="doc-{f['id']}" class="doc-section {is_active}">
            {converted}
        </div>
        """
        
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Project Documentation</title>
         {CSS}
    </head>
    <body>
        <div id="sidebar">
            <div id="sidebar-header">School Planner Docs</div>
            <div id="nav">
                {nav_html}
            </div>
        </div>
        <div id="content">
            {content_html}
        </div>
        {SCRIPT}
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"Documentation generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()
