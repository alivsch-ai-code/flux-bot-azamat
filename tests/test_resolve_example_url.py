from main import _resolve_example_url


def test_resolve_example_url_finds_http_in_nested_dicts():
    example = {
        "meta": {
            "output": [
                {"url": "https://example.com/preview.jpg"},
            ]
        }
    }
    assert _resolve_example_url(example) == "https://example.com/preview.jpg"


def test_resolve_example_url_returns_output_image_candidate_first():
    example = {
        "output_image": "https://example.com/a.png",
        "image": "https://example.com/b.png",
        "url": "https://example.com/c.png",
    }
    assert _resolve_example_url(example) == "https://example.com/a.png"

