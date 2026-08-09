# -*- coding: utf-8 -*-
import re

initiate_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html'
return_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html'
forward_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'

with open(initiate_path, 'r', encoding='utf-8') as f:
    initiate_content = f.read()

# Extract the entire tinymce.init block from initiate_notesheet.html
init_match = re.search(r'tinymce\.init\(\{.*?(?=// CUSTOM FLAGS BUTTON)', initiate_content, re.DOTALL)
if not init_match:
    print("Could not find tinymce.init in initiate")
    exit(1)

init_code = init_match.group(0)

def replace_in_file(path, selector):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'tinymce\.init\(\{.*?(?=// CUSTOM FLAGS BUTTON)', content, re.DOTALL)
    if match:
        # replace the selector in the copied code
        new_init_code = init_code.replace("selector: '#agenda_details',", f"selector: '{selector}',")
        
        # also we need to handle the textarea and btn references in setup.
        # in initiate: initializeTinyMCE(btn, textarea) 
        # the setup block uses textarea and btn, which are captured in the closure of initializeTinyMCE.
        # This is exactly the same for return_notesheet.
        
        new_content = content[:match.start()] + new_init_code + content[match.end():]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated " + path)
    else:
        print("Could not find target tinymce.init block in " + path)

replace_in_file(return_path, '#remark')
replace_in_file(forward_path, '#forward_remark')
