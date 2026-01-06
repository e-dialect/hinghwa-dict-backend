"""
Custom widgets for Django admin interface to enhance content editing and display.

This module provides:
- MarkdownEditorWidget: A markdown editor with preview for TextField
- AudioPlayerWidget: An audio player widget for URLField containing audio files
"""

from django import forms
from django.utils.safestring import mark_safe


class MarkdownEditorWidget(forms.Textarea):
    """
    A custom widget that provides a markdown editor with live preview.
    Uses EasyMDE (SimpleMDE successor) for markdown editing.
    """

    def __init__(self, attrs=None):
        default_attrs = {"class": "markdown-editor"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/easymde@latest/dist/easymde.min.css",
            )
        }
        js = ("https://cdn.jsdelivr.net/npm/easymde@latest/dist/easymde.min.js",)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        textarea_id = attrs.get("id", f"id_{name}") if attrs else f"id_{name}"

        # JavaScript to initialize the markdown editor
        js = f"""
        <script>
        (function() {{
            if (typeof EasyMDE !== 'undefined') {{
                var textarea = document.getElementById('{textarea_id}');
                if (textarea && !textarea.easyMDEInstance) {{
                    var easyMDE = new EasyMDE({{
                        element: textarea,
                        spellChecker: false,
                        toolbar: ["bold", "italic", "heading", "|", 
                                  "quote", "unordered-list", "ordered-list", "|",
                                  "link", "image", "|", 
                                  "preview", "side-by-side", "fullscreen", "|",
                                  "guide"],
                        placeholder: "请输入Markdown格式的内容...",
                        status: ["lines", "words", "cursor"],
                        renderingConfig: {{
                            codeSyntaxHighlighting: true,
                        }}
                    }});
                    textarea.easyMDEInstance = easyMDE;
                }}
            }}
        }})();
        </script>
        """
        return mark_safe(html + js)


class AudioPlayerWidget(forms.URLInput):
    """
    A custom widget that displays an audio player for audio file URLs.
    Shows both the URL input field and a playable audio player.
    """

    def __init__(self, attrs=None):
        default_attrs = {"class": "vURLField"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)

        # Add audio player if there's a value
        if value:
            audio_player = f"""
            <div style="margin-top: 10px;">
                <audio controls preload="metadata" style="width: 100%; max-width: 500px;">
                    <source src="{value}" type="audio/mpeg">
                    <source src="{value}" type="audio/wav">
                    <source src="{value}" type="audio/ogg">
                    您的浏览器不支持音频播放。
                </audio>
            </div>
            """
            html = html + audio_player

        return mark_safe(html)
