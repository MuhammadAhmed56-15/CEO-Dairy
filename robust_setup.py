# -*- coding: utf-8 -*-
import re

files = [
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html',
    r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html'
]

setup_logic = """setup: function (editor) {
          editor.on('init', function () {
            textarea.style.display = 'none';
            richEditorActive = true;
            btn.style.display = 'none';

            // PROFESSIONAL LETTERHEAD - AUTOMATIC INJECTION                
            const plainText = editor.getContent({ format: 'text' }).trim();
            const currentHtml = editor.getContent();
            const wsspLogo = '/static/images/wssp_logo_new.png?v=' + Date.now();
            const kpkLogo = '/static/images/kpk_emblem.png?v=' + Date.now();

            const letterhead = '<table style="width:100%;border-collapse:collapse;margin-bottom:14pt;padding:0;border:none;">' +
              '<tr>' +
              '<td style="width:90px;text-align:center;vertical-align:middle;padding:8pt 6pt 8pt 0;">' +
              '<img src="' + wsspLogo + '" alt="WSSP Logo" style="width:70px;height:70px;object-fit:contain;" />' +
              '</td>' +
              '<td style="text-align:center;vertical-align:middle;padding:8pt 4pt;">' +
              '<p style="font-weight:bold;font-size:10pt;margin:0 0 2pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;white-space:nowrap;">OFFICE OF THE CHIEF EXECUTIVE OFFICER (CEO) WATER &amp; SANITATION SERVICES,</p>' +
              '<p style="font-weight:bold;font-size:10pt;margin:0 0 5pt;font-family:Calibri,Arial,sans-serif;color:#4a5568;letter-spacing:0;">PESHAWAR, LOCAL GOVERNMENT COMPLEX, KHYBER PAKHTUNKHWA.</p>' +
              '<p style="font-size:9pt;margin:0 0 2pt;font-family:Calibri,Arial,sans-serif;color:#6b7280;">Plot # 33, Street No. 13, Sector E-8, Phase-VII, Hayatabad,</p>' +
              '<p style="font-size:9pt;margin:0;font-family:Calibri,Arial,sans-serif;color:#6b7280;"><strong>E mail: </strong><u style="color:#059669;">wsspeshawar@gmail.com</u>&nbsp;&nbsp;&nbsp;<strong>Phone #</strong> 091-9219018</p>' +
              '</td>' +
              '<td style="width:90px;text-align:center;vertical-align:middle;padding:8pt 0 8pt 6pt;">' +
              '<img src="' + kpkLogo + '" alt="KPK Emblem" style="width:70px;height:70px;object-fit:contain;" />' +
              '</td>' +
              '</tr>' +
              '</table>' +
              '<hr style="border:none;border-top:2px solid #8b4513;margin:0 0 15pt 0;padding:0;" />' +
              '<p>&nbsp;</p>';

            if (!plainText) {
              editor.setContent(letterhead);
            } else if (plainText.indexOf('CHIEF EXECUTIVE OFFICER') === -1) {
              editor.setContent(letterhead + currentHtml);
            }
            
            // Move cursor below letterhead
            editor.selection.select(editor.getBody(), true);
            editor.selection.collapse(false);
          });
"""

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'setup:\s*function\s*\(editor\)\s*\{.*?\}\s*\);\s*editor\.on\(\'change', content, re.DOTALL)
    if match:
        new_content = content[:match.start()] + setup_logic + "\n          editor.on('change" + content[match.end():]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Fixed ' + path)
    else:
        print('Could not match in ' + path)

