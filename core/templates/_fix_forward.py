"""
Build forward_notesheet.html from return_notesheet.html with these changes:
1. Header text: Return -> Forward
2. Form id: return-form -> forward-notesheet-form
3. Info banner text
4. Remark label text
5. Textarea placeholder
6. Add 'Forward To' section + select-wrapper CSS
7. Submit button: btn--danger -> btn--forward (with forward icon + text)
8. Submit sync: return-form -> forward-notesheet-form
9. bg-icon SVG: arrow forward instead of arrow return
"""
import sys

src = r"c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\return_notesheet.html"
dst = r"c:\Users\Hp\Desktop\python Work\ceo_commitment_dairy\core\templates\forward_notesheet.html"

with open(src, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Header badge
text = text.replace("Return Document", "Forward Document")

# 2. Title
text = text.replace('id="return-title"', 'id="forward-title"')
text = text.replace("aria-labelledby=\"return-title\"", "aria-labelledby=\"forward-title\"")
text = text.replace(">Return Notesheet</h1>", ">Forward Notesheet</h1>")

# 3. Form id
text = text.replace('id="return-form"', 'id="forward-notesheet-form"')

# 4. Info banner text
old_banner = 'You are returning <strong>{{ notesheet.title }}</strong>. The remark you provide will be recorded in the return history and will be visible to the original sender.'
new_banner = """You are forwarding <strong>{{ notesheet.title }}</strong>.
              {%% if existing_flag_count > 0 %%}
              This notesheet already has <strong>{{ existing_flag_count }} flag(s)</strong>,
              <strong>{{ existing_annexure_count }} annexure(s)</strong>, and
              <strong>{{ existing_puc_count }} PUC(s)</strong> already assigned.
              Any new attachments will continue from the next available sequence.
              {%% else %%}
              Add a remark and choose the next recipient below.
              {%% endif %%}"""
# Use %% to avoid Python format string issues, then replace back
new_banner = new_banner.replace("%%", "%")
text = text.replace(old_banner, new_banner)

# 5. Remark section title
text = text.replace("Remarks &amp; Feedback", "Remarks &amp; Forwarding Notes")

# 6. Remark label
text = text.replace("Return reason / Correction notes", "Remark / Forwarding Notes")

# 7. Textarea placeholder
text = text.replace(
    'Describe the reason for returning this notesheet, or specify the corrections required...',
    'Enter forwarding remarks, comments or instructions here...'
)

# 8. Field hint
text = text.replace(
    'This field is mandatory before submitting the return request.',
    'This field is mandatory before forwarding the notesheet.'
)

# 9. Add btn--forward CSS (replace btn--danger)
old_btn_css = """  .btn--danger {
    background: var(--color-danger-500);
    border-color: var(--color-danger-500);
    color: white;
  }
  .btn--danger:hover {
    background: var(--color-danger-700);
    border-color: var(--color-danger-700);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }"""

new_btn_css = """  .btn--forward {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-color: transparent;
    color: white;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    padding: var(--space-3) var(--space-6);
    font-size: 0.9375rem;
  }
  .btn--forward:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(37, 99, 235, 0.45);
  }"""

text = text.replace(old_btn_css, new_btn_css)

# 10. Add select-wrapper CSS before .form-actions
select_css = """  /* ── Forward To Select ── */
  .select-wrapper {
    position: relative;
    margin-top: var(--space-3);
  }

  .select-wrapper .select-icon {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--color-gray-400);
    font-size: 1rem;
    pointer-events: none;
    z-index: 1;
  }

  .select-wrapper select {
    width: 100%;
    padding: 0.9rem 2.8rem 0.9rem 2.8rem;
    font-family: var(--font-sans);
    font-size: 0.9375rem;
    font-weight: 400;
    color: var(--color-gray-900);
    background: white;
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-xl);
    outline: none;
    cursor: pointer;
    -webkit-appearance: none;
    box-shadow: var(--shadow-sm);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='9' viewBox='0 0 14 9'%3E%3Cpath d='M1 1l6 6 6-6' stroke='%231e3a5f' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 1rem center;
  }
  .select-wrapper select:hover { border-color: var(--color-gray-400); }
  .select-wrapper select:focus {
    border-color: var(--color-primary-500);
    box-shadow: var(--shadow-glow);
  }

"""

text = text.replace("  .form-actions {", select_css + "  .form-actions {")

# 11. Add Forward To section before form-actions HTML
forward_to_section = """
          <!-- ── Forward To Section ── -->
          <section class="section" aria-labelledby="forward-to-heading">
            <div class="section__header">
              <div class="section__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </div>
              <h2 id="forward-to-heading" class="section__title">Forward To</h2>
            </div>

            <div class="field-label">
              Select Recipient
              <span class="field-label__required" aria-label="required">*</span>
            </div>

            <div class="select-wrapper">
              <span class="select-icon">\U0001f464</span>
              <select id="forwarded_to" name="forwarded_to" required aria-required="true" style="width: max-content; max-width: 100%;">
                <option value="" disabled selected>Select recipient\u2026</option>
                {%% for user in users %%}
                <option value="{{ user.id }}">{{ user.username }} \u2014 {{ user.profile.role }}</option>
                {%% endfor %%}
              </select>
            </div>
          </section>

"""
forward_to_section = forward_to_section.replace("%%", "%")

# Insert before the form-actions div
text = text.replace(
    '          <div class="section form-actions">',
    forward_to_section + '          <div class="section form-actions">'
)

# 12. Replace submit button (Return -> Forward)
old_submit = """            <button type="submit" class="btn btn--danger" aria-label="Confirm and return notesheet">
              <svg class="btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 9.5H7.14m3.74-3.74L7.14 9.5l3.74 3.74"/>
              </svg>
              Return Notesheet
            </button>"""

new_submit = """            <button type="submit" class="btn btn--forward" aria-label="Confirm and forward notesheet">
              <svg class="btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
              Forward Notesheet
            </button>"""

text = text.replace(old_submit, new_submit)

# 13. Cancel label
text = text.replace('aria-label="Cancel return"', 'aria-label="Cancel forward"')

# 14. bg-icon SVG: use forward arrow
old_bg_svg = '<path d="M20 9.5H7.14m3.74-3.74L7.14 9.5l3.74 3.74"/>'
new_bg_svg = '<path d="M5 12h14M12 5l7 7-7 7"/>'
# Only replace the first occurrence (in the header bg-icon)
text = text.replace(old_bg_svg, new_bg_svg, 1)

# 15. Fix submit sync form id
text = text.replace(
    "document.getElementById('return-form')",
    "document.getElementById('forward-notesheet-form')"
)

with open(dst, "w", encoding="utf-8") as f:
    f.write(text)

lines = text.splitlines()
print(f"forward_notesheet.html written successfully! ({len(lines)} lines)")
