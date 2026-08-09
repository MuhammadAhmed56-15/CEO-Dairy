import sys

def get_modal_block(content):
    start_str = '<!-- Preview Modal -->'
    start_idx = content.find(start_str)
    if start_idx == -1:
        return None, -1, -1
    
    end_str = '<div class="page-container'
    end_idx = content.find(end_str, start_idx)
    
    if end_idx == -1:
        # fallback to script tag
        end_str = '<script>'
        end_idx = content.find(end_str, start_idx)
    
    if end_idx != -1:
        # Step back from end_idx to remove the empty lines if possible, or just replace up to end_idx
        return content[start_idx:end_idx], start_idx, end_idx
    return None, -1, -1

files = {
    'return': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    'initiate': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    'forward': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'
}

with open(files['return'], 'r', encoding='utf-8') as f:
    return_content = f.read()

return_modal, _, _ = get_modal_block(return_content)

if not return_modal:
    sys.exit('Could not find modal in return_notesheet.html')

for name in ['initiate', 'forward']:
    path = files[name]
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    _, start_idx, end_idx = get_modal_block(content)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + return_modal + content[end_idx:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Successfully replaced modal in ' + name)
    else:
        print('Could not find modal in ' + name)
