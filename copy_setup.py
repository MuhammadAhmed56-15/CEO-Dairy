# -*- coding: utf-8 -*-
import re

initiate_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html'
return_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html'
forward_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'

with open(initiate_path, 'r', encoding='utf-8') as f:
    initiate_content = f.read()

# Extract the exact setup block from initiate_notesheet.html
setup_match = re.search(r'setup:\s*function\s*\(editor\)\s*\{.*?\}\s*\);\s*editor\.on\(\'change input keyup\'', initiate_content, re.DOTALL)

if not setup_match:
    print("Could not find setup block in initiate_notesheet.html")
    exit(1)

setup_code = setup_match.group(0).replace("          editor.on('change input keyup'", "")

def replace_in_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'setup:\s*function\s*\(editor\)\s*\{.*?\}\s*\);\s*editor\.on\(\'change input keyup\'', content, re.DOTALL)
    if match:
        new_content = content[:match.start()] + setup_code + "\n          editor.on('change input keyup'" + content[match.end():]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated " + path)
    else:
        print("Could not find target setup block in " + path)

replace_in_file(return_path)
replace_in_file(forward_path)
