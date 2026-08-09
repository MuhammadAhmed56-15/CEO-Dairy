import os
from django import template

register = template.Library()

@register.filter
def file_name(value):
    if value:
        return os.path.basename(value.name)
    return ''

@register.filter
def file_icon(value):
    if not value:
        return 'fas fa-file-alt file-generic'
    
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext == '.pdf':
        return 'fas fa-file-pdf file-pdf'
    elif ext in ['.doc', '.docx']:
        return 'fas fa-file-word file-word'
    elif ext in ['.xls', '.xlsx']:
        return 'fas fa-file-excel file-excel'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        return 'fas fa-file-image file-image'
    elif ext in ['.ppt', '.pptx']:
        return 'fas fa-file-powerpoint file-powerpoint'
    else:
        return 'fas fa-file-alt file-generic'
