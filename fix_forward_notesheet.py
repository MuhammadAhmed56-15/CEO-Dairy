# -*- coding: utf-8 -*-
import re

# Read the working return_notesheet.html to copy its correct initializeTinyMCE
with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html', 'r', encoding='utf-8') as f:
    return_content = f.read()

# Extract the entire initializeTinyMCE function from return_notesheet.html
# It starts at "function initializeTinyMCE" and ends at the closing brace of the outer function
match = re.search(r'function initializeTinyMCE\(btn, textarea\) \{.*?\n  \}', return_content, re.DOTALL)
if not match:
    print("ERROR: Could not find initializeTinyMCE in return_notesheet.html")
    exit(1)

return_func = match.group(0)
# Change selector from #remark to #forward_remark
forward_func = return_func.replace("selector: '#remark',", "selector: '#forward_remark',")
print("Return func found, length:", len(return_func))

# Now read forward_notesheet.html
with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html', 'r', encoding='utf-8') as f:
    forward_content = f.read()

# Find and replace the initializeTinyMCE function in forward_notesheet.html
fwd_match = re.search(r'function initializeTinyMCE\(btn, textarea\) \{.*?\n  \}', forward_content, re.DOTALL)
if not fwd_match:
    print("ERROR: Could not find initializeTinyMCE in forward_notesheet.html")
    exit(1)

print("Forward func found, length:", len(fwd_match.group(0)))
new_content = forward_content[:fwd_match.start()] + forward_func + forward_content[fwd_match.end():]

with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: forward_notesheet.html fixed!")

# Verify
checks = ['setup: function (editor)', 'PROFESSIONAL LETTERHEAD', 'wsspLogo', 'kpkLogo', "selector: '#forward_remark'"]
with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html', 'r', encoding='utf-8') as f:
    verify = f.read()
for c in checks:
    print(f"  {c}: {'OK' if c in verify else 'MISSING!'}")
