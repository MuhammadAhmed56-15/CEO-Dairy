import re

with open('core/templates/ceo_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace CEO with Manager
html = html.replace('CEO Dashboard', 'Manager Dashboard')
html = html.replace('📊 CEO Dashboard Overview', '📊 Manager Dashboard Overview')

# Remove commitment option
html = re.sub(r'<option value="commitment">Commitments</option>\s*', '', html)

with open('core/templates/manager_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Dashboard copied and updated.')
