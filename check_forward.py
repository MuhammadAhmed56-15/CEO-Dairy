import re

with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if any(kw in stripped for kw in ['setup: function', 'PROFESSIONAL LETTERHEAD', 'editor.on(\'init', 'quickbars_insert_toolbar', 'richEditorActive = true']):
        print(f"Line {i}: {line[:120]}")
