import os
import unittest
from unittest.mock import patch

from AudioCompare.InputFile import resolve_lame_executable


class ResolveLameExecutableTests(unittest.TestCase):
    @patch("AudioCompare.InputFile.shutil.which")
    def test_uses_lame_from_path_by_default(self, which):
        which.return_value = "/usr/bin/lame"

        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_lame_executable(), "/usr/bin/lame")

        which.assert_called_once_with("lame")

    @patch("AudioCompare.InputFile.shutil.which")
    def test_uses_configured_executable(self, which):
        which.return_value = "/opt/audio/bin/lame"

        with patch.dict(
            os.environ, {"LAME_EXECUTABLE": "/opt/audio/bin/lame"}, clear=True
        ):
            self.assertEqual(resolve_lame_executable(), "/opt/audio/bin/lame")

        which.assert_called_once_with("/opt/audio/bin/lame")

    @patch("AudioCompare.InputFile.shutil.which", return_value=None)
    def test_missing_executable_has_actionable_error(self, which):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError, "install LAME on PATH or set LAME_EXECUTABLE"
            ):
                resolve_lame_executable()

        which.assert_called_once_with("lame")
