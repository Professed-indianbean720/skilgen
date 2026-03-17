import os
import unittest

from skilgen.agents.model_registry import resolve_model_settings
from skilgen.core.models import SkilgenConfig


class ModelRegistryTests(unittest.TestCase):
    def test_resolve_model_settings_uses_provider_defaults(self) -> None:
        config = SkilgenConfig(
            include_paths=["."],
            exclude_paths=[],
            domains_override=[],
            skill_depth=2,
            update_trigger="manual",
            langsmith_project=None,
            model_provider="openai",
            model="gpt-5",
            api_key_env=None,
        )
        settings = resolve_model_settings(config)
        self.assertEqual(settings.provider, "openai")
        self.assertEqual(settings.model, "gpt-5")
        self.assertEqual(settings.api_key_env, "OPENAI_API_KEY")

    def test_resolve_model_settings_reports_api_key_presence(self) -> None:
        os.environ["TEST_MODEL_KEY"] = "present"
        config = SkilgenConfig(
            include_paths=["."],
            exclude_paths=[],
            domains_override=[],
            skill_depth=2,
            update_trigger="manual",
            langsmith_project=None,
            model_provider="custom",
            model="local-model",
            api_key_env="TEST_MODEL_KEY",
        )
        settings = resolve_model_settings(config)
        self.assertTrue(settings.api_key_present)


if __name__ == "__main__":
    unittest.main()
