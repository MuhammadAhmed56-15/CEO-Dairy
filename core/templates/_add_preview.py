import os

def process_file(filepath, label_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'previewModalOverlay' in text:
        print(f"Already processed: {filepath}")
        return

    with open('preview_css.txt', 'r', encoding='utf-8') as f:
        css = f.read()
    with open('preview_html.txt', 'r', encoding='utf-8') as f:
        html = f.read()
    with open('preview_js.txt', 'r', encoding='utf-8') as f:
        js = f.read().replace("'agenda_details'", "'remark'")

    # 1. Inject CSS
    text = text.replace('</style>', f'\n{css}\n</style>')

    # 2. Inject HTML
    text = text.replace('<div class="page-container">', f'\n{html}\n<div class="page-container">')

    # 3. Inject JS
    text = text.replace('</script>\n\n{% endblock %}', f'\n{js}\n</script>\n\n{{% endblock %}}')

    # 4. Inject Preview Button
    old_btn_html = '''              <button type="button" id="toggle-rich-editor" class="btn-toggle-formatting">
                ✍️ Formatting Tools
              </button>
            </div>'''
    new_btn_html = '''              <button type="button" id="toggle-rich-editor" class="btn-toggle-formatting">
                ✍️ Formatting Tools
              </button>
              <button type="button" id="preview-btn" class="btn-toggle-formatting" style="margin-left: 0.5rem; background: var(--color-primary-600); color: white; border-color: var(--color-primary-700);">
                👁️ Preview
              </button>
            </div>'''
    text = text.replace(old_btn_html, new_btn_html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Successfully processed: {filepath}")

base_dir = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates'
process_file(os.path.join(base_dir, 'return_notesheet.html'), 'Return reason')
process_file(os.path.join(base_dir, 'forward_notesheet.html'), 'Remark / Forwarding Notes')
