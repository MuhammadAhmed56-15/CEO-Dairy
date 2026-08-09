import os

filepaths = [
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\view_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\edit_commitment.html',
]

def fix_mojibake(s):
    try:
        # Convert the mojibake string back to bytes using cp1252
        # then decode those bytes as utf-8
        b = s.encode('cp1252')
        return b.decode('utf-8')
    except Exception as e:
        return s

replacements = {
    'â˜°': '☰',
    'âœ ï¸ ': '✏️',
    'ðŸ‘ ï¸ ': '👁️',
    'ðŸš©': '🚩',
    'âš ï¸ ': '⚠️',
    'â• ': '═',
    'â”€â”€': '──',
    'Ã°Å¸â€œâ€ž': '📄',
    'Ã¢Å“â€¢': '✕',
    'â”€': '─'
}

for fp in filepaths:
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()
        
        changed = False
        for k, v in replacements.items():
            if k in text:
                text = text.replace(k, v)
                changed = True
                
        if changed:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'Fixed {os.path.basename(fp)}')
