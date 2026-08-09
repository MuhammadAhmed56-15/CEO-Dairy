import re
import sys

files = {
    'return': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    'initiate': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html',
    'forward': r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'
}

def get_style_block(content):
    style_match = re.search(r'<style>.*?</style>', content, re.DOTALL)
    if style_match:
        return style_match.group(0), style_match.start(), style_match.end()
    return None, -1, -1

with open(files['return'], 'r', encoding='utf-8') as f:
    return_content = f.read()

style_str, _, _ = get_style_block(return_content)

# Find where .preview-modal-overlay starts
start_preview = style_str.find('.preview-modal-overlay')
if start_preview == -1:
    sys.exit('Could not find .preview-modal-overlay in return_notesheet.html')

# Walk backwards to find the nearest comment or just grab from .preview-modal-overlay
start_comment = style_str.rfind('/*', 0, start_preview)
if start_comment == -1:
    start_comment = start_preview

end_style = style_str.find('</style>')
return_preview_css = style_str[start_comment:end_style]

for name in ['initiate', 'forward']:
    with open(files[name], 'r', encoding='utf-8') as f:
        content = f.read()
    
    style_str2, start_idx, end_idx = get_style_block(content)
    if not style_str2:
        print('Could not find style block in', name)
        continue
    
    sp = style_str2.find('.preview-modal-overlay')
    if sp != -1:
        sc = style_str2.rfind('/*', 0, sp)
        if sc == -1: sc = sp
        es = style_str2.find('</style>')
        
        new_style = style_str2[:sc] + return_preview_css + '\n  ' + style_str2[es:]
        new_content = content[:start_idx] + new_style + content[end_idx:]
        
        with open(files[name], 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Successfully replaced preview modal CSS in ' + name)
    else:
        print('Could not find .preview-modal-overlay in ' + name)
