import re
import os

new_table = """<table style="width:100%;border-collapse:collapse;margin-bottom:18pt;padding:0;border:none;">
  <tr>
    <td style="width:145px;text-align:center;vertical-align:middle;padding:12pt 10pt 12pt 0;">
      <img src="${window.location.origin}/static/images/wssp_logo_new.png" alt="WSSP Logo" draggable="false" style="width:135px;height:135px;object-fit:contain;user-select:none;" />
    </td>
    <td style="text-align:center;vertical-align:middle;padding:12pt 8pt;">
      <p style="font-weight:900 !important;font-size:18pt !important;margin:0 0 6pt;font-family:Calibri,Arial,sans-serif;color:#2d3748;letter-spacing:0.4px;line-height:1.5;">OFFICE OF THE CHIEF EXECUTIVE OFFICER (CEO) WATER &amp; SANITATION SERVICES,</p>
      <p style="font-weight:900 !important;font-size:18pt !important;margin:0 0 10pt;font-family:Calibri,Arial,sans-serif;color:#2d3748;letter-spacing:0.4px;line-height:1.5;">PESHAWAR, LOCAL GOVERNMENT COMPLEX, KHYBER PAKHTUNKHWA.</p>
      <p style="font-size:16pt !important;font-weight:bold !important;margin:0 0 6pt;font-family:Calibri,Arial,sans-serif;color:#1a202c;line-height:1.5;">Plot # 33, Street No. 13, Sector E-8, Phase-VII, Hayatabad,</p>
      <p style="font-size:16pt !important;font-weight:bold !important;margin:0;font-family:Calibri,Arial,sans-serif;color:#1a202c;line-height:1.5;"><strong>E mail: </strong><u style="color:#1d4ed8 !important;">wsspeshawar@gmail.com</u>&nbsp;&nbsp;&nbsp;&nbsp;<strong>Phone #</strong> 091-9219018</p>
    </td>
    <td style="width:145px;text-align:center;vertical-align:middle;padding:12pt 0 12pt 10pt;">
      <img src="${window.location.origin}/static/images/kpk_emblem.png" alt="KPK Emblem" draggable="false" style="width:135px;height:135px;object-fit:contain;user-select:none;" />
    </td>
  </tr>
</table>"""

files_to_update = [
    r"c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\initiate_notesheet.html",
    r"c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html",
    r"c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html"
]

pattern = re.compile(r'<table style="width:100%;border-collapse:collapse;margin-bottom:14pt;padding:0;border:none;">.*?</table>', re.DOTALL)

for file_path in files_to_update:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = pattern.findall(content)
    print(f"Found {len(matches)} matches in {os.path.basename(file_path)}")

    new_content = pattern.sub(new_table, content)

    # Let's also make sure we only match inside openPreview or previewPrintBtn areas to be safe.
    # Actually, the 14pt margin table is VERY specific to this letterhead preview.
    
    # Also add draggable="false" to TinyMCE injected images inside initializeTinyMCE?
    # Wait, the user specifically mentioned the PREVIEW is moving around. TinyMCE is fine.

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(file_path)}")
    else:
        print(f"No changes made to {os.path.basename(file_path)}")
