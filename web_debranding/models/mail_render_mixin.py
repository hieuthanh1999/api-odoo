# Copyright 2019 O4SB - Graeme Gellatly
# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Onestein - Andrea Stirpe
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import re

from lxml import etree, html

from odoo import api, models

from .ir_config_parameter import get_debranding_parameters_env

def debrand_links(source, new_website):
    return re.sub(r"\bwww.odoo.com\b", new_website, source, flags=re.IGNORECASE)

class MailRenderMixin(models.AbstractModel):
    _inherit = "mail.render.mixin"

    def remove_href_odoo(
        self, value, remove_parent=True, remove_before=False, to_keep=None
    ):
        if len(value) < 20:
            return value
        # value can be bytes type; ensure we get a proper string
        if type(value) is bytes:
            value = value.decode()
        has_odoo_link = re.search(r"<a\s(.*)odoo\.com", value, flags=re.IGNORECASE)

        if has_odoo_link:
            params = get_debranding_parameters_env(self.env)
            new_name = params.get("web_debranding.new_name")
            new_website = params.get("web_debranding.new_website")
            value = debrand_links(value, new_website)
        return value

    @api.model
    def _render_template(
        self,
        template_src,
        model,
        res_ids,
        engine="qweb_view",
        add_context=None,
        options=None,
        post_process=False,
    ):
        """replace anything that is with odoo in templates
        if is a <a that contains odoo will delete it completely
        original:
         Render the given string on records designed by model / res_ids using
        the given rendering engine.

        :param str template_src: template text to render (jinja) or  (qweb)
          this could be cleaned but hey, we are in a rush
        :param str model: model name of records on which we want to perform rendering
        :param list res_ids: list of ids of records (all belonging to same model)
        :param string engine: jinja
        :param post_process: perform rendered str / html post processing (see
          ``_render_template_postprocess``)

        :return dict: {res_id: string of rendered template based on record}"""
        orginal_rendered = super()._render_template(
            template_src,
            model,
            res_ids,
            engine=engine,
            add_context=add_context,
            post_process=post_process,
        )

        for key in res_ids:
            orginal_rendered[key] = self.remove_href_odoo(orginal_rendered[key])

        return orginal_rendered
