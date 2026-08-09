import re

def get_init(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'tinymce\.init\(\{.*?(?=setup:\s*function)', content, re.DOTALL)
    return match.group(0) if match else ""

initiate_init = get_init(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html')
return_init = get_init(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html')

if initiate_init == return_init:
    print("TinyMCE init config is identical.")
else:
    print("Differences found!")
    # Let's write them to files to see the diff easily
    with open('init_i.txt', 'w', encoding='utf-8') as f: f.write(initiate_init)
    with open('init_r.txt', 'w', encoding='utf-8') as f: f.write(return_init)
    print("Wrote to init_i.txt and init_r.txt")
