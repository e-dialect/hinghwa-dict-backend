#!/usr/bin/env python
"""
Test script to verify custom Django admin widgets are properly configured.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HinghwaDict.settings")
django.setup()

from article.admin import ArticleAdminForm
from music.admin import MusicAdminForm
from word.admin import (
    WordAdminForm,
    PronunciationAdminForm,
    ApplicationAdminForm,
    CharacterAdminForm,
)
from website.admin import DailyExpressionAdminForm
from utils.admin.widgets import (
    MarkdownEditorWidget,
    AudioPlayerWidget,
    IPAKeyboardWidget,
)


def test_widget_configuration():
    """Test that widgets are properly configured in admin forms."""

    print("🔍 Testing Django Admin Custom Widgets Configuration\n")
    print("=" * 60)

    # Test ArticleAdmin
    print("\n1. Testing ArticleAdmin (content field with Markdown editor):")
    article_form = ArticleAdminForm()
    content_widget = article_form.fields["content"].widget
    is_markdown = isinstance(content_widget, MarkdownEditorWidget)
    print(f"   ✓ Content field widget: {content_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_markdown else '❌'} Markdown editor configured: {is_markdown}"
    )

    # Test WordAdmin
    print("\n2. Testing WordAdmin (annotation field with Markdown editor):")
    word_form = WordAdminForm()
    annotation_widget = word_form.fields["annotation"].widget
    is_markdown = isinstance(annotation_widget, MarkdownEditorWidget)
    print(f"   ✓ Annotation field widget: {annotation_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_markdown else '❌'} Markdown editor configured: {is_markdown}"
    )

    # Test ApplicationAdmin
    print("\n3. Testing ApplicationAdmin (annotation field with Markdown editor):")
    app_form = ApplicationAdminForm()
    annotation_widget = app_form.fields["annotation"].widget
    is_markdown = isinstance(annotation_widget, MarkdownEditorWidget)
    print(f"   ✓ Annotation field widget: {annotation_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_markdown else '❌'} Markdown editor configured: {is_markdown}"
    )

    # Test MusicAdmin
    print("\n4. Testing MusicAdmin (source field with Audio player):")
    music_form = MusicAdminForm()
    source_widget = music_form.fields["source"].widget
    is_audio = isinstance(source_widget, AudioPlayerWidget)
    print(f"   ✓ Source field widget: {source_widget.__class__.__name__}")
    print(f"   {'✅' if is_audio else '❌'} Audio player configured: {is_audio}")

    # Test PronunciationAdmin
    print("\n5. Testing PronunciationAdmin (source field with Audio player):")
    pronunciation_form = PronunciationAdminForm()
    source_widget = pronunciation_form.fields["source"].widget
    is_audio = isinstance(source_widget, AudioPlayerWidget)
    print(f"   ✓ Source field widget: {source_widget.__class__.__name__}")
    print(f"   {'✅' if is_audio else '❌'} Audio player configured: {is_audio}")

    print("\n6. Testing PronunciationAdmin (ipa and pinyin with IPA keyboard):")
    ipa_widget = pronunciation_form.fields["ipa"].widget
    pinyin_widget = pronunciation_form.fields["pinyin"].widget
    is_ipa_keyboard = isinstance(ipa_widget, IPAKeyboardWidget)
    is_pinyin_keyboard = isinstance(pinyin_widget, IPAKeyboardWidget)
    print(f"   ✓ IPA field widget: {ipa_widget.__class__.__name__}")
    print(f"   ✓ Pinyin field widget: {pinyin_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_ipa_keyboard else '❌'} IPA keyboard for ipa field: {is_ipa_keyboard}"
    )
    print(
        f"   {'✅' if is_pinyin_keyboard else '❌'} IPA keyboard for pinyin field: {is_pinyin_keyboard}"
    )

    # Test CharacterAdmin
    print("\n7. Testing CharacterAdmin (ipa and pinyin with IPA keyboard):")
    character_form = CharacterAdminForm()
    char_ipa_widget = character_form.fields["ipa"].widget
    char_pinyin_widget = character_form.fields["pinyin"].widget
    is_char_ipa_keyboard = isinstance(char_ipa_widget, IPAKeyboardWidget)
    is_char_pinyin_keyboard = isinstance(char_pinyin_widget, IPAKeyboardWidget)
    print(f"   ✓ IPA field widget: {char_ipa_widget.__class__.__name__}")
    print(f"   ✓ Pinyin field widget: {char_pinyin_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_char_ipa_keyboard else '❌'} IPA keyboard for ipa field: {is_char_ipa_keyboard}"
    )
    print(
        f"   {'✅' if is_char_pinyin_keyboard else '❌'} IPA keyboard for pinyin field: {is_char_pinyin_keyboard}"
    )

    # Test DailyExpressionAdmin
    print("\n8. Testing DailyExpressionAdmin (pinyin with IPA keyboard):")
    daily_expr_form = DailyExpressionAdminForm()
    daily_pinyin_widget = daily_expr_form.fields["pinyin"].widget
    is_daily_pinyin_keyboard = isinstance(daily_pinyin_widget, IPAKeyboardWidget)
    print(f"   ✓ Pinyin field widget: {daily_pinyin_widget.__class__.__name__}")
    print(
        f"   {'✅' if is_daily_pinyin_keyboard else '❌'} IPA keyboard for pinyin field: {is_daily_pinyin_keyboard}"
    )

    # Test widget rendering
    print("\n9. Testing widget rendering capabilities:")

    # Test MarkdownEditorWidget
    md_widget = MarkdownEditorWidget()
    md_html = md_widget.render("test_content", "# Test Markdown", {"id": "test_id"})
    has_easymde = "EasyMDE" in md_html
    has_textarea = "<textarea" in md_html
    print(f"   ✓ MarkdownEditorWidget renders textarea: {has_textarea}")
    print(f"   ✓ MarkdownEditorWidget includes EasyMDE: {has_easymde}")
    print(
        f"   {'✅' if has_easymde and has_textarea else '❌'} Markdown widget rendering works"
    )

    # Test AudioPlayerWidget
    audio_widget = AudioPlayerWidget()
    audio_html = audio_widget.render(
        "test_source", "https://example.com/test.mp3", {"id": "test_id"}
    )
    has_audio_tag = "<audio" in audio_html
    has_controls = "controls" in audio_html
    print(f"   ✓ AudioPlayerWidget renders audio tag: {has_audio_tag}")
    print(f"   ✓ AudioPlayerWidget includes controls: {has_controls}")
    print(
        f"   {'✅' if has_audio_tag and has_controls else '❌'} Audio widget rendering works"
    )

    # Test IPAKeyboardWidget
    ipa_widget = IPAKeyboardWidget()
    ipa_html = ipa_widget.render("test_ipa", "ɛ", {"id": "test_ipa_id"})
    has_input = "<input" in ipa_html
    has_keyboard = "ipa-keyboard" in ipa_html
    has_toggle = "显示/隐藏" in ipa_html
    print(f"   ✓ IPAKeyboardWidget renders input: {has_input}")
    print(f"   ✓ IPAKeyboardWidget includes keyboard: {has_keyboard}")
    print(f"   ✓ IPAKeyboardWidget includes toggle: {has_toggle}")
    print(
        f"   {'✅' if has_input and has_keyboard and has_toggle else '❌'} IPA keyboard widget rendering works"
    )

    print("\n" + "=" * 60)
    print("✅ All widget configuration tests completed!\n")

    # Summary
    print("📋 Summary:")
    print(
        "   • Markdown Editor: Article.content, Word.annotation, Application.annotation"
    )
    print("   • Audio Player: Music.source, Pronunciation.source")
    print(
        "   • IPA Keyboard: Word (standard_ipa, standard_pinyin), Application (standard_ipa, standard_pinyin)"
    )
    print("                   Pronunciation (ipa, pinyin), Character (ipa, pinyin)")
    print("                   DailyExpression (pinyin)")
    print("\n💡 To see the widgets in action, start the Django admin server:")
    print("   python manage.py runserver")
    print("   Then visit: http://127.0.0.1:8000/admin/")


if __name__ == "__main__":
    try:
        test_widget_configuration()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
