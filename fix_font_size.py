# -*- coding: utf-8 -*-
# Increase letterhead font sizes in all three notesheet files

files = [
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html',
]

# Old -> New font size replacements inside the letterhead table
replacements = [
    # Main bold lines: 10pt -> 14pt
    ('font-size:10pt;margin:0 0 2pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;white-space:nowrap;',
     'font-size:14pt;margin:0 0 3pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;white-space:nowrap;'),
    ('font-size:10pt;margin:0 0 5pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;',
     'font-size:14pt;margin:0 0 5pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;'),
    # Address line: 9pt -> 11pt
    ('font-size:9pt;margin:0 0 2pt;font-family:Calibri,Arial,sans-serif;color:#6b7280;',
     'font-size:11pt;margin:0 0 2pt;font-family:Calibri,Arial,sans-serif;color:#6b7280;'),
    # Email/phone line: 9pt -> 11pt
    ('font-size:9pt;margin:0;font-family:Calibri,Arial,sans-serif;color:#6b7280;',
     'font-size:11pt;margin:0;font-family:Calibri,Arial,sans-serif;color:#6b7280;'),
    # Also make logos bigger: 70px -> 85px
    ('style="width:70px;height:70px;object-fit:contain;"',
     'style="width:85px;height:85px;object-fit:contain;"'),
]

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed = True
    
    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated: ' + path.split('\\')[-1])
    else:
        print('No changes needed: ' + path.split('\\')[-1])

print('Done!')
