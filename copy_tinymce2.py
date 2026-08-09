import re

initiate_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html'
return_path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html'

with open(initiate_path, 'r', encoding='utf-8') as f:
    initiate_content = f.read()

# Extract everything from tinymce.init({ down to the end of the config object (before the closing }); )
# It is better to use a simple string replacement.
# Let's extract the tinymce.init block from initiate:
init_match = re.search(r'tinymce\.init\(\{.*?\n\s*\}\);', initiate_content, re.DOTALL)
if not init_match:
    print("Could not find tinymce.init in initiate")
    exit(1)
init_code = init_match.group(0)

with open(return_path, 'r', encoding='utf-8') as f:
    return_content = f.read()

return_match = re.search(r'tinymce\.init\(\{.*?\n\s*\}\);', return_content, re.DOTALL)
if return_match:
    new_init = init_code.replace("selector: '#agenda_details',", "selector: '#remark',")
    new_content = return_content[:return_match.start()] + new_init + return_content[return_match.end():]
    with open(return_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated return_notesheet.html")
else:
    print("Could not find tinymce.init in return")

