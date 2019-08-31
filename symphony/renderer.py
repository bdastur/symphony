#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jinja2


def render_j2_template(templatefile, searchpath, obj):
    """Render a Jinja2 template and return the rendered string"""
    rendered_data = None
    template_loader = jinja2.FileSystemLoader(searchpath=searchpath)
    env = jinja2.Environment(
        loader=template_loader, trim_blocks=False, lstrip_blocks=False
    )
    template = env.get_template(templatefile)
    rendered_data = template.render(obj)

    return rendered_data
