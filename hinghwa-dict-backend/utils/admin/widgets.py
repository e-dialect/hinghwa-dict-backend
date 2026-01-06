"""
Custom widgets for Django admin interface to enhance content editing and display.

This module provides:
- MarkdownEditorWidget: A markdown editor with preview for TextField
- AudioPlayerWidget: An audio player widget for URLField containing audio files
- ImagePreviewWidget: An image preview widget for URLField containing image URLs
- IPAKeyboardWidget: An IPA keyboard widget for phonetic input in text fields
"""

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html, escape
from django.utils.translation import gettext_lazy as _


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
            "all": ("https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.css",)
        }
        js = ("https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.js",)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        textarea_id = escape(attrs.get("id", f"id_{name}") if attrs else f"id_{name}")

        # JavaScript to initialize the markdown editor
        js = format_html(
            """
        <script>
        (function() {{
            if (typeof EasyMDE !== 'undefined') {{
                var textarea = document.getElementById('{}');
                if (textarea && !textarea.easyMDEInstance) {{
                    var easyMDE = new EasyMDE({{
                        element: textarea,
                        spellChecker: false,
                        toolbar: ["bold", "italic", "heading", "|", 
                                  "quote", "unordered-list", "ordered-list", "|",
                                  "link", "image", "|", 
                                  "preview", "side-by-side", "fullscreen", "|",
                                  "guide"],
                        placeholder: "{}",
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
        """,
            textarea_id,
            _("请输入Markdown格式的内容..."),
        )
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
            escaped_value = escape(value)
            audio_player = format_html(
                """
            <div style="margin-top: 10px;">
                <audio controls preload="metadata" style="width: 100%; max-width: 500px;">
                    <source src="{}" type="audio/mpeg">
                    <source src="{}" type="audio/wav">
                    <source src="{}" type="audio/ogg">
                    {}
                </audio>
            </div>
            """,
                escaped_value,
                escaped_value,
                escaped_value,
                _("您的浏览器不支持音频播放。"),
            )
            html = html + audio_player

        return mark_safe(html)


class ImagePreviewWidget(forms.URLInput):
    """
    A custom widget that displays an image preview for image URL fields.
    Shows both the URL input field and a preview of the image.
    """

    def __init__(self, attrs=None, max_width=300, max_height=300):
        default_attrs = {"class": "vURLField"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
        self.max_width = max_width
        self.max_height = max_height

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)

        # Add image preview if there's a value
        if value:
            escaped_value = escape(value)
            image_preview = format_html(
                """
            <div style="margin-top: 10px;">
                <img src="{}" alt="{}" style="max-width: {}px; max-height: {}px; border: 1px solid #ddd; border-radius: 4px; padding: 5px; display: block;" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <p style="display: none; color: #666; font-style: italic;">{}</p>
            </div>
            """,
                escaped_value,
                _("图片预览"),
                self.max_width,
                self.max_height,
                _("图片加载失败或URL无效"),
            )
            html = html + image_preview

        return mark_safe(html)


class IPAKeyboardWidget(forms.TextInput):
    """
    A custom widget that provides an IPA keyboard for easy input of IPA symbols,
    pinyin characters, and other phonetic notations.

    Features clickable buttons organized by category:
    - IPA consonants and vowels
    - Nasalized vowels
    - Numeric superscripts
    - Dictionary pinyin scheme
    - BUC (Bàng-uâ-cê) romanization
    """

    def __init__(self, attrs=None):
        default_attrs = {"class": "vTextField ipa-keyboard-input"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        textarea_id = escape(attrs.get("id", f"id_{name}") if attrs else f"id_{name}")

        # Include CSS with a unique ID so browser can deduplicate
        # Using an ID ensures CSS is only applied once even if multiple widgets render
        css = """
        <style id="ipa-keyboard-styles">
        .ipa-keyboard {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        .ipa-keyboard-section {
            margin-bottom: 10px;
        }
        .ipa-keyboard-section:last-child {
            margin-bottom: 0;
        }
        .ipa-keyboard-title {
            font-weight: bold;
            font-size: 13px;
            margin-bottom: 5px;
            color: #495057;
            display: block;
        }
        .ipa-keyboard-btn {
            display: inline-block;
            padding: 6px 10px;
            margin: 3px 4px;
            background: #fff;
            border: 2px solid #ced4da;
            border-radius: 4px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 500;
            transition: all 0.15s ease;
            user-select: none;
            min-width: 35px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .ipa-keyboard-btn:hover {
            background: #e3f2fd;
            border-color: #007bff;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,123,255,0.2);
        }
        .ipa-keyboard-btn:active {
            transform: scale(0.96) translateY(0);
            background: #007bff;
            color: white;
            border-color: #0056b3;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1) inset;
        }
        .ipa-keyboard-btn-clicked {
            animation: btnClick 0.3s ease;
        }
        @keyframes btnClick {
            0% {
                background: #007bff;
                color: white;
                border-color: #0056b3;
                transform: scale(0.96);
            }
            100% {
                background: #fff;
                color: inherit;
                border-color: #ced4da;
                transform: scale(1);
            }
        }
        .ipa-keyboard-toggle {
            cursor: pointer;
            color: #007bff;
            text-decoration: underline;
            font-size: 12px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .ipa-keyboard-toggle:hover {
            color: #0056b3;
        }
        .ipa-keyboard-content {
            display: none;
        }
        .ipa-keyboard-content.visible {
            display: block;
        }
        </style>
        """

        # IPA character groups as specified in the issue
        ipa_consonants = ["ʰ", "ʦ", "ɬ", "θ", "ŋ", "β", "ɣ", "ʔ", "Ø"]
        ipa_vowels = ["ɛ", "ø", "ɒ", "œ", "ɵ", "ə", "ɯ", "ɐ", "æ", "ᴇ", "ɤ"]
        ipa_nasalized = [
            "ã",
            "ẽ",
            "ĩ",
            "ø̃",
            "ỹ",
            "ɒ̃",
            "ũ",
            "ɔ̃",
            "ɛ̃",
            "œ̃",
            "ɐ̃",
            "õ",
        ]
        numeric_superscripts = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸"]
        dict_pinyin = ["ü", "ñ", "ệ", "ẹ", "ê", "ô"]
        buc_lowercase = [
            "á",
            "â",
            "a̍",
            "ā",
            "é",
            "ê",
            "e̍",
            "ē",
            "í",
            "î",
            "i̍",
            "ī",
            "ó",
            "ô",
            "o̍",
            "ō",
            "ú",
            "û",
            "u̍",
            "ū",
            "a̤",
            "á̤",
            "â̤",
            "a̤̍",
            "ā̤",
            "e̤",
            "é̤",
            "ê̤",
            "e̤̍",
            "ē̤",
            "o̤",
            "ó̤",
            "ô̤",
            "o̤̍",
            "ō̤",
            "ṳ",
            "ṳ́",
            "ṳ̂",
            "ṳ̍",
            "ṳ̄",
            "ń",
            "n̂",
            "n̍",
            "n̄",
            "ⁿ",
        ]
        buc_uppercase = [
            "Á",
            "Â",
            "A̍",
            "Ā",
            "É",
            "Ê",
            "E̍",
            "Ē",
            "Í",
            "Î",
            "I̍",
            "Ī",
            "Ó",
            "Ô",
            "O̍",
            "Ō",
            "Ú",
            "Û",
            "U̍",
            "Ū",
            "A̤",
            "Á̤",
            "Â̤",
            "A̤̍",
            "Ā̤",
            "E̤",
            "É̤",
            "Ê̤",
            "E̤̍",
            "Ē̤",
            "O̤",
            "Ó̤",
            "Ô̤",
            "O̤̍",
            "Ō̤",
            "Ṳ",
            "Ṳ́",
            "Ṳ̂",
            "Ṳ̍",
            "Ṳ̄",
            "Ń",
            "N̂",
            "N̍",
            "N̄",
            "ᴺ",
        ]

        # Create keyboard HTML
        keyboard_html = format_html(
            """
        <div class="ipa-keyboard" id="ipa-keyboard-{}">
            <span class="ipa-keyboard-toggle" onclick="toggleIPAKeyboard('{}')">
                📝 显示/隐藏 IPA 拼音键盘
            </span>
            <div class="ipa-keyboard-content" id="ipa-keyboard-content-{}">
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">国际音标 (IPA) - 辅音:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">国际音标 (IPA) - 元音:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">国际音标 (IPA) - 鼻化:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">数字上标:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">大词典拼音方案:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">平话字 (BUC) - 小写:</span>
                    <div>
                        {}
                    </div>
                </div>
                <div class="ipa-keyboard-section">
                    <span class="ipa-keyboard-title">平话字 (BUC) - 大写:</span>
                    <div>
                        {}
                    </div>
                </div>
            </div>
        </div>
        """,
            textarea_id,
            textarea_id,
            textarea_id,
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in ipa_consonants
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in ipa_vowels
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in ipa_nasalized
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in numeric_superscripts
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in dict_pinyin
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in buc_lowercase
                )
            ),
            mark_safe(
                "".join(
                    format_html(
                        "<span class=\"ipa-keyboard-btn\" onclick=\"insertIPAChar('{}', '{}', event)\">{}</span>",
                        textarea_id,
                        escape(char),
                        char,
                    )
                    for char in buc_uppercase
                )
            ),
        )

        # JavaScript for keyboard functionality
        js = format_html(
            """
        <script>
        (function() {{
            if (!window.toggleIPAKeyboard) {{
                window.toggleIPAKeyboard = function(inputId) {{
                    var content = document.getElementById('ipa-keyboard-content-' + inputId);
                    if (content.classList.contains('visible')) {{
                        content.classList.remove('visible');
                    }} else {{
                        content.classList.add('visible');
                    }}
                }};
            }}
            
            if (!window.insertIPAChar) {{
                window.insertIPAChar = function(inputId, char, event) {{
                    var input = document.getElementById(inputId);
                    if (!input) return;
                    
                    // Add visual feedback to the clicked button
                    var button = event ? event.target : null;
                    if (button) {{
                        button.classList.add('ipa-keyboard-btn-clicked');
                        setTimeout(function() {{
                            button.classList.remove('ipa-keyboard-btn-clicked');
                        }}, 300);
                    }}
                    
                    // Get current cursor position
                    var startPos = input.selectionStart;
                    var endPos = input.selectionEnd;
                    var value = input.value;
                    
                    // Insert character at cursor position
                    input.value = value.substring(0, startPos) + char + value.substring(endPos);
                    
                    // Set cursor position after inserted character
                    var newPos = startPos + char.length;
                    input.setSelectionRange(newPos, newPos);
                    
                    // Focus back on input
                    input.focus();
                    
                    // Trigger input event for Django admin change detection
                    var inputEvent = new Event('input', {{ bubbles: true }});
                    input.dispatchEvent(inputEvent);
                }};
            }}
        }})();
        </script>
        """
        )

        return mark_safe(css + html + keyboard_html + js)
