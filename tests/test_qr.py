from mapvalidator.qr import IMPORT_ENDPOINT, build_import_uri


def test_encodes_full_url():
    uri = build_import_uri("https://example.com/a/b.zip?x=1")
    assert uri == (
        "tak://com.atakmap.app/import?url="
        "https%3A%2F%2Fexample.com%2Fa%2Fb.zip%3Fx%3D1"
    )


def test_has_import_endpoint_prefix():
    assert build_import_uri("https://x").startswith(IMPORT_ENDPOINT + "?url=")


def test_slashes_and_colons_are_encoded_not_raw():
    uri = build_import_uri("https://a.com/p")
    # The inner URL's scheme separator must be encoded, not left literal.
    assert "://a.com" not in uri
    assert "url=https%3A%2F%2Fa.com%2Fp" in uri
