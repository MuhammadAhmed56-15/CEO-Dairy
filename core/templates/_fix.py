import os

filepaths = [
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\view_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\edit_commitment.html',
]

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
    'â”€': '─',
    'Ã°Å¸â€™Â¡': '💡',
    'Ã¢â€œËœ': 'ⓘ',
    'Ã°Å¸â€œÂ ': '📌',
    'ðŸ“ ': '📄',
    'ðŸ“©': '📄',
    'ðŸ‘€': '👀'
}

for fp in filepaths:
    if os.path.exists(fp):
        with open(fp, 'rb') as f:
            b = f.read()
        try:
            text = b.decode('utf-8')
        except UnicodeDecodeError:
            text = b.decode('cp1252', errors='replace')
        
        changed = False
        for k, v in replacements.items():
            if k in text:
                text = text.replace(k, v)
                changed = True
                
        if changed:
            with open(fp, 'wb') as f:
                f.write(text.encode('utf-8'))
            print('Fixed', os.path.basename(fp))
