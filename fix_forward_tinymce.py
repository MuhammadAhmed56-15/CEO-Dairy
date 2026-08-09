import re

initiate_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html'
forward_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'

def extract_function(code, func_name):
    start_idx = code.find(func_name)
    if start_idx == -1: return None
    
    brace_count = 0
    in_func = False
    for i in range(start_idx, len(code)):
        if code[i] == '{':
            brace_count += 1
            in_func = True
        elif code[i] == '}':
            brace_count -= 1
        
        if in_func and brace_count == 0:
            return code[start_idx:i+1]
    return None

with open(initiate_path, 'r', encoding='utf-8') as f:
    initiate_content = f.read()

initiate_func = extract_function(initiate_content, 'function initializeTinyMCE(btn, textarea) {')
if initiate_func:
    print('Found initiate_func of length:', len(initiate_func))
    initiate_func = initiate_func.replace("selector: '#agenda_details'", "selector: '#remark'")

with open(forward_path, 'r', encoding='utf-8') as f:
    forward_content = f.read()

start_idx = forward_content.find('function initializeTinyMCE(btn, textarea) {')
end_idx = forward_content.find('window.addEventListener(\'DOMContentLoaded\'')

if start_idx != -1 and end_idx != -1:
    print('Replacing block in forward_notesheet')
    new_content = forward_content[:start_idx] + initiate_func + '\n\n  ' + forward_content[end_idx:]
    with open(forward_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Fix applied successfully to forward_notesheet.html')
else:
    print('Could not find bounds in forward_notesheet')
