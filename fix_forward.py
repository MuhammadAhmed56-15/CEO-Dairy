# -*- coding: utf-8 -*-
import re

path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

checks = ['setup: function (editor)', 'PROFESSIONAL LETTERHEAD', 'wsspLogo']
for c in checks:
    print(f'{c}: {c in content}')

if 'setup: function (editor)' not in content or 'PROFESSIONAL LETTERHEAD' not in content:
    print("Needs fix!")
    # Find the selector to know which textarea id is used
    sel_match = re.search(r"selector: '#(\w+)'", content)
    selector_id = sel_match.group(1) if sel_match else 'unknown'
    print(f"Selector ID: {selector_id}")
else:
    print("Already has setup and letterhead - OK!")
