with open(r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_css = text.find('.preview-modal-overlay')
end_css = text.find('</style>', start_css)
with open('preview_css.txt', 'w', encoding='utf-8') as f:
    f.write(text[start_css:end_css])

start_html = text.find('<!-- Preview Modal -->')
end_html = text.find('<div class="page-wrapper">', start_html)
with open('preview_html.txt', 'w', encoding='utf-8') as f:
    f.write(text[start_html:end_html])

start_js = text.find('function openPreview()')
end_js = text.find('  /* ── Auto-save to draft ── */', start_js)
if end_js == -1: end_js = text.find('</script>', start_js)
with open('preview_js.txt', 'w', encoding='utf-8') as f:
    f.write(text[start_js:end_js])
print("Done")
