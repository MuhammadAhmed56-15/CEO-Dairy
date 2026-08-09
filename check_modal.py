import re

files = {
    'initiate': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    'forward': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'
}

for name, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    start_idx = content.find('<!-- Preview Modal -->')
    if start_idx != -1:
        # Find the end of the modal (div id="previewModalOverlay")
        # Just grab about 1500 chars to see what it is
        print(f'--- {name} ---')
        print(content[start_idx:start_idx+1000])
