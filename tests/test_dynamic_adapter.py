"""Tests für src.infrastructure.ai.dynamic_adapter – DynamicSchemaAdapter."""
from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter


class TestBuildInputPayload:
    """Prüft build_input_payload: Payload-Erstellung aus Schema und User-Input."""

    def test_empty_schema_returns_prompt_only(self):
        """Leeres Schema liefert nur {'prompt': user_prompt}."""
        adapter = DynamicSchemaAdapter()
        result = adapter.build_input_payload({}, "hello")
        assert result == {"prompt": "hello"}

    def test_none_schema_returns_prompt_only(self):
        """None-Schema liefert nur prompt."""
        adapter = DynamicSchemaAdapter()
        result = adapter.build_input_payload(None, "test")
        assert result == {"prompt": "test"}

    def test_applies_defaults(self):
        """Schema-Defaults werden gesetzt."""
        adapter = DynamicSchemaAdapter()
        schema = {
            "properties": {
                "prompt": {"type": "string"},
                "width": {"type": "integer", "default": 1024},
            }
        }
        result = adapter.build_input_payload(schema, "cat")
        assert result["prompt"] == "cat"
        assert result["width"] == 1024

    def test_maps_prompt_via_alias(self):
        """Prompt wird per Alias (text, caption, etc.) gefunden."""
        adapter = DynamicSchemaAdapter()
        schema = {"properties": {"text": {"type": "string"}}}
        result = adapter.build_input_payload(schema, "a dog")
        assert result["text"] == "a dog"

    def test_kwargs_mapped_to_schema(self):
        """Extra kwargs werden ins Schema gemappt."""
        adapter = DynamicSchemaAdapter()
        schema = {
            "properties": {
                "prompt": {"type": "string"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
            }
        }
        result = adapter.build_input_payload(
            schema, "photo", width=512, height=768
        )
        assert result["width"] == 512
        assert result["height"] == 768

    def test_maps_input_reference_as_image(self):
        """`input_reference` wird wie ein Bild-Feld gemappt."""
        adapter = DynamicSchemaAdapter()
        schema = {
            "properties": {
                "prompt": {"type": "string"},
                # Replicate-Schemas sind nicht immer exakt; darum ohne `format: uri`.
                "input_reference": {"type": "string"},
            }
        }
        file_urls = ["https://example.com/reference.jpg"]
        result = adapter.build_input_payload(schema, "hello", file_urls=file_urls)
        assert result["prompt"] == "hello"
        assert result["input_reference"] == file_urls[0]

    def test_maps_unknown_extensionless_url_to_video_slot(self):
        """URLs ohne Extension sollen auch für Video-Slots mappen (z. B. CDN-URLs)."""
        adapter = DynamicSchemaAdapter()
        schema = {
            "properties": {
                "prompt": {"type": "string"},
                "input_video": {"type": "string", "format": "uri"},
            }
        }
        # Keine Dateiendung -> unknown.
        file_urls = ["https://example.com/blob/abcdef123456"]
        result = adapter.build_input_payload(schema, "go", file_urls=file_urls)
        assert result["input_video"] == file_urls[0]

    def test_maps_unknown_extensionless_url_to_audio_slot(self):
        """URLs ohne Extension sollen auch für Audio-Slots mappen."""
        adapter = DynamicSchemaAdapter()
        schema = {
            "properties": {
                "prompt": {"type": "string"},
                "input_audio": {"type": "string", "format": "uri"},
            }
        }
        file_urls = ["https://cdn.example.org/media/stream123"]
        result = adapter.build_input_payload(schema, "voice", file_urls=file_urls)
        assert result["input_audio"] == file_urls[0]


class TestParseOutput:
    """Prüft parse_output: Extraktion von URL/Text aus API-Antworten."""

    def test_list_of_strings_returns_first(self):
        """Liste von Strings liefert ersten Eintrag."""
        adapter = DynamicSchemaAdapter()
        assert adapter.parse_output(["https://a.com/1", "https://a.com/2"]) == "https://a.com/1"

    def test_empty_list_returns_none(self):
        """Leere Liste liefert None."""
        adapter = DynamicSchemaAdapter()
        assert adapter.parse_output([]) is None

    def test_dict_with_output_key(self):
        """Dict mit 'output' liefert output-Wert."""
        adapter = DynamicSchemaAdapter()
        data = {"output": "https://x.com/img.png"}
        assert adapter.parse_output(data) == "https://x.com/img.png"

    def test_dict_with_video_key(self):
        """Dict mit 'video' liefert video-Wert."""
        adapter = DynamicSchemaAdapter()
        data = {"video": "https://v.com/v.mp4"}
        assert adapter.parse_output(data) == "https://v.com/v.mp4"

    def test_dict_with_image_key(self):
        """Dict mit 'image' liefert image-Wert."""
        adapter = DynamicSchemaAdapter()
        data = {"image": "https://i.com/i.jpg"}
        assert adapter.parse_output(data) == "https://i.com/i.jpg"

    def test_dict_with_url_key(self):
        """Dict mit 'url' liefert url-Wert."""
        adapter = DynamicSchemaAdapter()
        data = {"url": "https://u.com/f"}
        assert adapter.parse_output(data) == "https://u.com/f"

    def test_string_passthrough(self):
        """String wird unverändert zurückgegeben."""
        adapter = DynamicSchemaAdapter()
        assert adapter.parse_output("https://direct.url") == "https://direct.url"
