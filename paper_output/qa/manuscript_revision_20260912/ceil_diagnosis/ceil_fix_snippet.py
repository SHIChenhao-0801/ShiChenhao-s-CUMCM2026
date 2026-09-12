"""Minimal tested ceiling-glyph repair; operates only on a supplied document.

This helper does not open or save any manuscript by itself.
Apply after mathematical run styling so that later formatting does not remove
the normal-text flag. The Unicode text and math expression stay unchanged.
"""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def repair_ceiling_glyphs(document):
    changed = 0
    for run in document.element.body.iter(qn('m:r')):
        text = ''.join(n.text or '' for n in run.findall(qn('m:t')))
        if text not in {'⌈', '⌉'}:
            continue
        properties = run.find(qn('m:rPr'))
        if properties is None:
            properties = OxmlElement('m:rPr')
            run.insert(0, properties)
        normal = properties.find(qn('m:nor'))
        if normal is None:
            normal = OxmlElement('m:nor')
            properties.append(normal)
        normal.set(qn('m:val'), '1')
        changed += 1
    return changed
