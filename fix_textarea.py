import re

path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the giant style string in textarea with a standard one
# Find <textarea id="remark"...
new_content = re.sub(
    r'<textarea id="remark" name="remark" class="form-input".*?</textarea>',
    '<textarea id="remark" name="remark" class="form-input"\n                  placeholder="Describe the reason for returning this notesheet, or specify the corrections required..."\n                  required rows="14"\n                  style="resize: vertical; min-height: 460px; font-family: Calibri, sans-serif; font-size: 1rem; line-height: 1.8;"></textarea>',
    content,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Fixed textarea styles in return_notesheet.html")
