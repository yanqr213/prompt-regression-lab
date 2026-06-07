import os
import unittest

from prompt_regression_lab.render import render_template


class RenderTemplateTests(unittest.TestCase):
    def test_render_replaces_variables(self):
        self.assertEqual(render_template("Hello {{ name }}", {"name": "Ada"}), "Hello Ada")

    def test_render_falls_back_to_environment(self):
        previous = os.environ.get("PRLAB_SAMPLE_ENV")
        os.environ["PRLAB_SAMPLE_ENV"] = "from-env"
        try:
            self.assertEqual(render_template("Value {{ PRLAB_SAMPLE_ENV }}", {}), "Value from-env")
        finally:
            if previous is None:
                os.environ.pop("PRLAB_SAMPLE_ENV", None)
            else:
                os.environ["PRLAB_SAMPLE_ENV"] = previous

    def test_render_keeps_unknown_placeholder(self):
        self.assertEqual(render_template("{{ missing }}", {}), "{{ missing }}")
