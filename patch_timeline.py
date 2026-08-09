import re

with open('core/templates/view_notesheet.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ns_body = """      {# Main Content Body - Unified Chronological Timeline #}
      <div class="ns-body">
        
        <section class="section" aria-labelledby="timeline-heading">
          <div class="section__header" style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">
            <div class="section__icon" aria-hidden="true" style="background: #10b981; color: white;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <h2 id="timeline-heading" class="section__title" style="font-size: 1.25rem;">Notesheet Timeline</h2>
          </div>

          <div class="timeline-container" style="display: flex; flex-direction: column; gap: 2rem;">
            
            {# 1. INITIATION BLOCK #}
            <div class="timeline-block" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
              <div class="timeline-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #cbd5e1; padding-bottom: 1rem; margin-bottom: 1rem;">
                <div class="forward-flow" style="display: flex; align-items: center; gap: 0.5rem; font-weight: 600;">
                  <span class="cell-user" style="color: #0f172a; font-size: 1rem;">{{ notesheet.created_by.username }}</span>
                  <span style="color: #64748b; font-size: 0.85rem; font-weight: 500;">(Initiator)</span>
                </div>
                <span class="attachment-row__meta" style="color: #64748b; font-size: 0.85rem;">Initiated on {{ notesheet.created_at|date:"d M Y · h:i A" }}</span>
              </div>
              
              <div class="timeline-content">
                {% if agendas %}
                  {% for agenda in agendas %}
                    <div style="margin-bottom: 1.5rem; color: #1e293b; line-height: 1.6;">
                      {{ agenda.agenda_title|safe }}
                    </div>
                  {% endfor %}
                {% else %}
                  <div style="color: #94a3b8; font-style: italic; margin-bottom: 1.5rem;">No agendas added.</div>
                {% endif %}

                {% if initial_attachments %}
                  <div class="action-attachments" style="margin-top: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden;">
                    <div class="action-attachments__label" style="background: #f1f5f9; padding: 0.75rem 1rem; font-weight: 600; color: #475569; font-size: 0.85rem; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; margin: 0;">Attachments</div>
                    <div class="action-attachments__list" style="display: flex; flex-direction: column; gap: 0;">
                      {% for att in initial_attachments %}
                      <div class="attachment-row" style="padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; {% if forloop.last %}border-bottom: none;{% endif %} margin: 0; background: white;">
                        <div class="attachment-row__info" style="display: flex; align-items: center; gap: 0.75rem;">
                          {% if att.flag_name %}
                            {% if "Flag" in att.flag_name %}
                            <span style="background: #ef4444; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                            {% elif "Annexure" in att.flag_name %}
                            <span style="background: #059669; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                            {% elif "PUC" in att.flag_name %}
                            <span style="background: #2563eb; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                            {% else %}
                            <span style="background: #e2e8f0; color: #334155; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                            {% endif %}
                          {% endif %}
                          <span class="attachment-row__name" style="font-weight: 500; color: #1e293b;">{{ att.file.name|cut:"notesheet_attachments/" }}</span>
                        </div>
                        <div class="attachment-row__actions" style="display: flex; align-items: center; gap: 1rem;">
                          <span class="attachment-row__meta" style="font-size: 0.75rem; color: #94a3b8;">{{ att.uploaded_at|date:"d M Y · h:i A" }}</span>
                          <a href="{{ att.file.url }}" target="_blank" class="attachment-link" style="color: #2563eb; font-weight: 600; font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 0.25rem;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            View
                          </a>
                        </div>
                      </div>
                      {% endfor %}
                    </div>
                  </div>
                {% endif %}
                
                {% if notesheet.created_by.profile.signature %}
                  <div class="signature-stamp-box" style="margin-top: 1.5rem; display: inline-block; padding: 1rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                    <div style="height: 60px; margin-bottom: 0.5rem;">
                      <img src="{{ notesheet.created_by.profile.signature.url }}" alt="Signature" style="max-height: 100%; object-fit: contain;">
                    </div>
                    <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">{{ notesheet.created_by.get_full_name|default:notesheet.created_by.username }}</div>
                    <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.5rem;">{{ notesheet.created_by.profile.role }} · Signed Digitally</div>
                    <div style="font-size: 0.75rem; color: #475569; font-weight: 600; display: inline-flex; align-items: center; gap: 0.4rem; background: #e2e8f0; padding: 0.25rem 0.5rem; border-radius: 4px;">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                      {{ notesheet.created_at|date:"d M Y · h:i A" }}
                    </div>
                  </div>
                {% endif %}
              </div>
            </div>

            {# 2. SUBSEQUENT TIMELINE BLOCKS (Forwards and Returns) #}
            {% for item in timeline %}
              <div class="timeline-block" style="background: #ffffff; border: 1px solid {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); position: relative;">
                
                <!-- Timeline Connector Line -->
                <div style="position: absolute; top: -2rem; left: 2rem; width: 2px; height: 2rem; background: #cbd5e1;"></div>

                <div class="timeline-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed {% if item.type == 'return' %}#fca5a5{% else %}#cbd5e1{% endif %}; padding-bottom: 1rem; margin-bottom: 1rem;">
                  <div class="forward-flow" style="display: flex; align-items: center; gap: 0.5rem; font-weight: 600;">
                    <span class="cell-user" style="color: #0f172a; font-size: 1rem;">{{ item.actor.username }}</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{% if item.type == 'return' %}#ef4444{% else %}#3b82f6{% endif %}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                    <span class="cell-user" style="color: {% if item.type == 'return' %}#ef4444{% else %}#3b82f6{% endif %}; font-size: 1rem;">{{ item.receiver.username }}</span>
                  </div>
                  <span class="attachment-row__meta" style="color: #64748b; font-size: 0.85rem;">
                    {% if item.type == 'return' %}Returned{% else %}Marked{% endif %} on {{ item.action_date|date:"d M Y · h:i A" }}
                  </span>
                </div>
                
                <div class="timeline-content">
                  <div class="cell-remark" style="color: #1e293b; line-height: 1.6; margin-bottom: 1.5rem;">
                    {% if item.clean_remark %}
                      {{ item.clean_remark|safe }}
                    {% else %}
                      <span style="color: #94a3b8; font-style: italic;">No remarks provided.</span>
                    {% endif %}
                  </div>

                  {% if item.rich_attachments %}
                    <div class="action-attachments" style="margin-top: 1rem; background: {% if item.type == 'return' %}#fef2f2{% else %}#f8fafc{% endif %}; border-radius: 8px; border: 1px solid {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; overflow: hidden;">
                      <div class="action-attachments__label" style="background: {% if item.type == 'return' %}#fee2e2{% else %}#f1f5f9{% endif %}; padding: 0.75rem 1rem; font-weight: 600; color: #475569; font-size: 0.85rem; text-transform: uppercase; border-bottom: 1px solid {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; margin: 0;">Attachments</div>
                      <div class="action-attachments__list" style="display: flex; flex-direction: column; gap: 0;">
                        {% for att in item.rich_attachments %}
                        <div class="attachment-row" style="padding: 0.75rem 1rem; border-bottom: 1px solid {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; {% if forloop.last %}border-bottom: none;{% endif %} margin: 0; background: white;">
                          <div class="attachment-row__info" style="display: flex; align-items: center; gap: 0.75rem;">
                            {% if att.flag_name %}
                              {% if "Flag" in att.flag_name %}
                              <span style="background: #ef4444; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                              {% elif "Annexure" in att.flag_name %}
                              <span style="background: #059669; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                              {% elif "PUC" in att.flag_name %}
                              <span style="background: #2563eb; color: white; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                              {% else %}
                              <span style="background: #e2e8f0; color: #334155; padding: 0.25rem 0.625rem; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{{ att.flag_name }}</span>
                              {% endif %}
                            {% endif %}
                            <span class="attachment-row__name" style="font-weight: 500; color: #1e293b;">{{ att.file.name|cut:"notesheet_attachments/" }}</span>
                          </div>
                          <div class="attachment-row__actions" style="display: flex; align-items: center; gap: 1rem;">
                            <span class="attachment-row__meta" style="font-size: 0.75rem; color: #94a3b8;">{{ att.uploaded_at|date:"d M Y · h:i A" }}</span>
                            <a href="{{ att.file.url }}" target="_blank" class="attachment-link" style="color: {% if item.type == 'return' %}#ef4444{% else %}#2563eb{% endif %}; font-weight: 600; font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 0.25rem;">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                              View
                            </a>
                          </div>
                        </div>
                        {% endfor %}
                      </div>
                    </div>
                  {% endif %}

                  {% if item.actor.profile.signature %}
                    <div class="signature-stamp-box" style="margin-top: 1.5rem; display: inline-block; padding: 1rem; background: {% if item.type == 'return' %}#fef2f2{% else %}#f8fafc{% endif %}; border: 1px solid {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; border-radius: 8px;">
                      <div style="height: 60px; margin-bottom: 0.5rem;">
                        <img src="{{ item.actor.profile.signature.url }}" alt="Signature" style="max-height: 100%; object-fit: contain;">
                      </div>
                      <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">{{ item.actor.get_full_name|default:item.actor.username }}</div>
                      <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.5rem;">{{ item.actor.profile.role }} · Signed Digitally</div>
                      <div style="font-size: 0.75rem; color: #475569; font-weight: 600; display: inline-flex; align-items: center; gap: 0.4rem; background: {% if item.type == 'return' %}#fecaca{% else %}#e2e8f0{% endif %}; padding: 0.25rem 0.5rem; border-radius: 4px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                        {{ item.action_date|date:"d M Y · h:i A" }}
                      </div>
                    </div>
                  {% endif %}
                </div>
              </div>
            {% endfor %}

          </div>
        </section>

      </div>
"""

# Replace everything from `{# Main Content Body #}` down to `</div>\n    </article>`
pattern = re.compile(r"\{\# Main Content Body \#\}.*?</div>\s*</article>", re.DOTALL)
replacement = new_ns_body + "\n    </article>"

new_content = pattern.sub(replacement, content)

with open('core/templates/view_notesheet.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully replaced ns-body with unified timeline layout")
