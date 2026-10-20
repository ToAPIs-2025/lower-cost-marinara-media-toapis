from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_marinara_flow as flow


class FlowTests(TestCase):
    def test_presets_match_proposed_top_level_contract(self):
        image, edit, video = flow.presets()
        self.assertEqual(image["request"], {"model": "gpt-image-2", "size": "16:9", "resolution": "1k", "n": 1})
        self.assertEqual(edit["pricing_conditions"]["input_image_count"], 1)
        self.assertEqual(video["request"]["duration"], 4)
        self.assertEqual(video["request"]["resolution"], "480p")
        self.assertFalse(video["request"]["generate_audio"])
        self.assertNotIn("input", video["request"])

    @patch.object(flow, "prepare", return_value={"estimated_usd": "0.2"})
    @patch.object(flow, "generate")
    def test_total_budget_checked_before_generation(self, generate, prepare):
        with self.assertRaisesRegex(ValueError, "Combined forecast"):
            flow.run_flow(object(), ".", maximum="0.50", live=True)
        generate.assert_not_called()

    @patch.object(flow, "quote_flow", return_value={"forecast_usd": "0.16"})
    @patch.object(flow, "generate")
    def test_quote_only_never_submits(self, generate, quote):
        self.assertEqual(flow.run_flow(object(), ".", live=False)["forecast_usd"], "0.16")
        generate.assert_not_called()

    @patch.object(flow, "quote_flow", return_value={})
    @patch.object(flow, "generate")
    def test_edit_uses_url_references_and_video_uses_edited_frame(self, generate, quote):
        generate.side_effect = [
            {"status": "completed", "output": "scene.png"},
            {"status": "completed", "output": "edited.png"},
            {"status": "completed", "output": "video.mp4"},
        ]
        client = SimpleNamespace(upload_png=lambda path: "https://example.com/uploaded-scene.png")
        result = flow.run_flow(client, ".", live=True)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["native_marinara_verified"])
        self.assertEqual(generate.call_args_list[1].args[1]["request"]["reference_images"],
                         ["https://example.com/uploaded-scene.png"])
        self.assertEqual(generate.call_args_list[2].kwargs["image"], Path("edited.png"))

    @patch.object(flow, "quote_flow", return_value={})
    @patch.object(flow, "generate", return_value={"status": "failed"})
    def test_failure_stops_dependent_paid_tasks(self, generate, quote):
        result = flow.run_flow(object(), ".", live=True)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(generate.call_count, 1)

    def test_upload_accepts_jpeg_and_caches_url(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "reference.jpg"
            source.write_bytes(b"\xff\xd8\xffjpeg-fixture")
            client = flow.ProjectClient.__new__(flow.ProjectClient)
            client.state = root
            with patch.object(client, "json", return_value={"data": {"url": "https://example.com/image.jpg"}}) as request:
                self.assertEqual(client.upload_png(source), "https://example.com/image.jpg")
                body = request.call_args.args[1]
                self.assertIn(b"Content-Type: image/jpeg", body)
                self.assertIn(b'name="file"', body)
                client.upload_png(source)
                self.assertEqual(request.call_count, 1)

    def test_invalid_image_rejected_before_upload(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "invalid.png"
            source.write_bytes(b"not-an-image")
            client = flow.ProjectClient.__new__(flow.ProjectClient)
            client.state = Path(folder)
            with patch.object(client, "json") as request:
                with self.assertRaisesRegex(ValueError, "Reference must"):
                    client.upload_png(source)
                request.assert_not_called()


if __name__ == "__main__":
    main()
