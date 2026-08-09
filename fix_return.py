# -*- coding: utf-8 -*-
import re

path = r'c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The broken block: from line 1147 paste_postprocess function (with wrong events inside it)
# to line 1190 (end of tinymce.init)
# We need to replace from `paste_postprocess` to the closing `});` with correct version

OLD_BLOCK = '''        /* ── ✂️ AUTO-CLEAN WORD PASTE ── */
        paste_postprocess: function (plugin, args) {
          var node = args.node;

          /* 1 ▸ Strip all mso-* / Word-only CSS properties */
          node.querySelectorAll('[style]').forEach(function (el) {
            var raw = el.getAttribute('style') || '';
            var cleaned = raw.split(';')
              .map(function (s) { return s.trim(); })
              .filter(function (s) {
                if (!s) return false;
                var prop = s.split(':')[0].trim().toLowerCase();
                return !prop.startsWith('mso-')
                  && prop !== 'tab-stops'
                  && prop !== 'layout-grid-mode'
                  && prop !== 'punctuation-wrap'
                  && prop !== 'text-autospace';
              })
              .join('; ');
            if (cleaned) { el.setAttribute('style', cleaned); }
            else { el.removeAttribute('style'); }
          });

          editor.on('change input keyup', function () {
            editor.save();
          });

          /* ── 🔒 CTRL+A: Select only content below letterhead ── */
          editor.on('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'a' || e.key === 'A')) {
              const body = editor.getBody();
              const hr = body.querySelector('hr');
              if (hr) {
                e.preventDefault();
                e.stopPropagation();
                const range = editor.dom.createRng();
                range.setStartAfter(hr);
                range.setEndAfter(body.lastChild);
                editor.selection.setRng(range);
                return false;
              }
            }
          });
        }
      });'''

NEW_BLOCK = '''        /* ── ✂️ AUTO-CLEAN WORD PASTE ── */
        paste_postprocess: function (plugin, args) {
          var node = args.node;

          /* 1 ▸ Strip all mso-* / Word-only CSS properties */
          node.querySelectorAll('[style]').forEach(function (el) {
            var raw = el.getAttribute('style') || '';
            var cleaned = raw.split(';')
              .map(function (s) { return s.trim(); })
              .filter(function (s) {
                if (!s) return false;
                var prop = s.split(':')[0].trim().toLowerCase();
                return !prop.startsWith('mso-')
                  && prop !== 'tab-stops'
                  && prop !== 'layout-grid-mode'
                  && prop !== 'punctuation-wrap'
                  && prop !== 'text-autospace';
              })
              .join('; ');
            if (cleaned) { el.setAttribute('style', cleaned); }
            else { el.removeAttribute('style'); }
          });
        },

        setup: function (editor) {
          editor.on('init', function () {
            textarea.style.display = 'none';
            richEditorActive = true;
            btn.style.display = 'none';

            // ╔═══════════════════════════════════════════════════════════════╗
            // ║ PROFESSIONAL LETTERHEAD - AUTOMATIC INJECTION                ║
            // ╚═══════════════════════════════════════════════════════════════╝
            const currentContent = editor.getContent({ format: 'text' }).trim();
            if (!currentContent) {
              const wsspLogo = '/static/images/wssp_logo_new.png?v=' + Date.now();
              const kpkLogo = '/static/images/kpk_emblem.png?v=' + Date.now();

              editor.setContent(
                '<table style="width:100%;border-collapse:collapse;margin-bottom:14pt;padding:0;border:none;">' +
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
                '<p>&nbsp;</p>'
              );
              editor.selection.select(editor.getBody(), true);
              editor.selection.collapse(false);
            }
          });
          editor.on('change input keyup', function () {
            editor.save();
          });

          /* ── 🔒 CTRL+A: Select only content below letterhead ── */
          editor.on('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'a' || e.key === 'A')) {
              const body = editor.getBody();
              const hr = body.querySelector('hr');
              if (hr) {
                e.preventDefault();
                e.stopPropagation();
                const range = editor.dom.createRng();
                range.setStartAfter(hr);
                range.setEndAfter(body.lastChild);
                editor.selection.setRng(range);
                return false;
              }
            }
          });
        }
      });'''

if OLD_BLOCK in content:
    new_content = content.replace(OLD_BLOCK, NEW_BLOCK)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Fixed return_notesheet.html")
else:
    print("ERROR: Target block not found. Checking what is there...")
    # show lines 1145-1192 area
    lines = content.split('\n')
    for i, line in enumerate(lines[1144:1195], start=1145):
        print(f"{i}: {line}")
