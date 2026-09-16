import os
import unittest
from unittest.mock import patch

import environ
from django.core.exceptions import ImproperlyConfigured

from HinghwaDict.security import (
    UNSAFE_DEVELOPMENT_SECRET_KEY,
    load_secret_key,
)


class SecretKeySettingsTests(unittest.TestCase):
    def test_production_requires_explicit_secret_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_key(environ.Env(), debug=False)

    def test_production_accepts_explicit_secret_key(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-production-key"}, clear=True):
            self.assertEqual(
                load_secret_key(environ.Env(), debug=False),
                "test-production-key",
            )

    def test_development_uses_explicitly_unsafe_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                load_secret_key(environ.Env(), debug=True),
                UNSAFE_DEVELOPMENT_SECRET_KEY,
            )

    def test_development_honors_explicit_secret_key(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-development-key"}, clear=True):
            self.assertEqual(
                load_secret_key(environ.Env(), debug=True),
                "test-development-key",
            )
