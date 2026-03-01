from deepvu.services.css_sanitizer import is_css_safe, sanitize_css


class TestSanitizeCSS:
    def test_strips_url(self) -> None:
        css = "body { background: url(http://evil.com); }"
        result = sanitize_css(css)
        assert "url(" not in result.replace("/* removed */", "")
        assert "/* removed */" in result

    def test_strips_import(self) -> None:
        css = '@import url("http://evil.com/styles.css");'
        result = sanitize_css(css)
        assert "@import" not in result.replace("/* removed */", "")
        assert "/* removed */" in result

    def test_strips_expression(self) -> None:
        css = "div { width: expression(alert('xss')); }"
        result = sanitize_css(css)
        assert "expression(" not in result.replace("/* removed */", "")
        assert "/* removed */" in result

    def test_strips_javascript(self) -> None:
        css = "div { background: javascript:alert('xss'); }"
        result = sanitize_css(css)
        assert "javascript:" not in result.replace("/* removed */", "")
        assert "/* removed */" in result

    def test_strips_behavior(self) -> None:
        css = "div { behavior: url(xss.htc); }"
        result = sanitize_css(css)
        assert "behavior:" not in result.replace("/* removed */", "")
        assert "/* removed */" in result

    def test_preserves_safe_css(self) -> None:
        css = "body { color: red; font-size: 14px; }"
        result = sanitize_css(css)
        assert result == css

    def test_is_css_safe_false(self) -> None:
        assert is_css_safe("body { background: url(http://evil.com); }") is False
        assert is_css_safe("@import url('styles.css');") is False
        assert is_css_safe("div { width: expression(alert()); }") is False
        assert is_css_safe("div { background: javascript:alert(); }") is False
        assert is_css_safe("div { behavior: url(xss.htc); }") is False
        assert is_css_safe("div { -moz-binding: url(xss.xml); }") is False
        assert is_css_safe("div { background: vbscript:alert(); }") is False

    def test_is_css_safe_true(self) -> None:
        assert is_css_safe("body { color: red; font-size: 14px; }") is True
        assert is_css_safe("h1 { margin: 0; padding: 10px; }") is True
        assert is_css_safe(".container { display: flex; }") is True
