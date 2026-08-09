import re

with open('core/templates/manager_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the Commitment KPIs section
content = re.sub(r'<!-- Commitment KPIs -->(.*?)(?=<!-- Notesheet KPIs -->)', '', content, flags=re.DOTALL)

# Remove the Commitment Content Section
content = re.sub(r'<!-- 1\. Commitments Section -->(.*?)(?=<!-- 2\. Notesheets Section -->)', '', content, flags=re.DOTALL)

# Remove the commitment variables in javascript
content = re.sub(r"const comCatLabels = \[.*?\];", "const comCatLabels = [];", content, flags=re.DOTALL)
content = re.sub(r"const comCatData = \[.*?\];", "const comCatData = [];", content, flags=re.DOTALL)

with open('core/templates/manager_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Cleaned manager dashboard from commitments.")
