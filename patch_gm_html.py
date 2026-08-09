with open('core/templates/manager_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Manager Dashboard with {{ user.profile.role }} Dashboard to make it dynamic and correct for GM or any other role that might use it (though we will statically put GM for now just to be safe based on request)
content = content.replace('Manager Dashboard Overview', '{{ user.profile.role|default:"GM" }} Dashboard Overview')
content = content.replace('Manager Dashboard', 'GM Dashboard')
content = content.replace('Manager', '{{ user.profile.role|default:"GM" }}')

with open('core/templates/gm_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Copied manager_dashboard.html to gm_dashboard.html and replaced Manager with GM")
