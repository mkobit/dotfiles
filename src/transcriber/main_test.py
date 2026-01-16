import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.transcriber.main import main


class TestTranscriber(unittest.TestCase):
    @patch("src.transcriber.main.WhisperModel")
    def test_transcription_cli(self, mock_whisper_model: MagicMock) -> None:
        """Test the CLI flow with mocked WhisperModel."""
        # Setup Mock Model Instance
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        # Setup Mock Transcribe Result
        # segments must be a generator or iterable
        mock_segment = MagicMock()
        mock_segment.text = "Hello world "
        mock_segment.end = 1.0

        mock_info = MagicMock()
        mock_info.duration = 1.0

        # transcribe returns (segments, info)
        mock_model_instance.transcribe.return_value = (
            iter([mock_segment]),
            mock_info,
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create dummy input file
            input_path = Path("test_audio.mp3")
            input_path.touch()  # Create empty file

            # Run CLI
            result = runner.invoke(main, [str(input_path), "--output", "output.md"])

            if result.exit_code != 0:
                print(result.output)

            self.assertEqual(result.exit_code, 0)

            # Verify Model Initialization
            mock_whisper_model.assert_called_once()
            # Check default args
            call_args = mock_whisper_model.call_args
            self.assertEqual(call_args[0][0], "base.en")  # positional arg model_size
            self.assertEqual(call_args[1]["device"], "auto")
            self.assertEqual(call_args[1]["compute_type"], "auto")

            # Verify Transcribe Call
            mock_model_instance.transcribe.assert_called_once()
            transcribe_args = mock_model_instance.transcribe.call_args
            # Click passes the path as provided, which might be relative or absolute
            # In isolated_filesystem, it's relative 'test_audio.mp3'
            self.assertEqual(transcribe_args[0][0], str(input_path))
            self.assertEqual(transcribe_args[1]["beam_size"], 5)

            # Verify Output Content
            output_content = Path("output.md").read_text()
            self.assertIn("Hello world", output_content)
            self.assertIn("size: base.en", output_content)  # From default template
            self.assertIn("duration_seconds: 1.0", output_content)

    @patch("src.transcriber.main.WhisperModel")
    def test_custom_template(self, mock_whisper_model: MagicMock) -> None:
        """Test using a custom Jinja2 template."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance
        mock_model_instance.transcribe.return_value = (
            iter([]),
            MagicMock(duration=0.0),
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            input_path = Path("input.wav")
            input_path.touch()

            template_path = Path("custom.j2")
            template_path.write_text(
                "CUSTOM TEMPLATE: {{ text }} | "
                "Duration: {{ metadata.file.duration_seconds }}"
            )

            result = runner.invoke(
                main, [str(input_path), "--template", str(template_path)]
            )

            self.assertEqual(result.exit_code, 0)
            self.assertIn("CUSTOM TEMPLATE:", result.output)
            self.assertIn("Duration: 0.0", result.output)


if __name__ == "__main__":
    unittest.main()
