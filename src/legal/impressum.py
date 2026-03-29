"""
Impressum / Anbieterkennzeichnung — Texte je Sprache.

Platzhalter (von build_imprint_placeholders in settings-Integration befüllt):
{legal_name}, {address}, {email}, {phone_block}, {reg_block}, {vat_block}, {responsible_block}
"""

from __future__ import annotations

_IMPRESSUM_DE = """IMPRESSUM

Angaben gemäß § 5 TMG (Telemediengesetz) bzw. § 55 RStV (Rundfunkstaatsvertrag), soweit anwendbar.

Diensteanbieter / Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:
{legal_name}

Anschrift:
{address}

Kontakt:
{email}
{phone_block}{responsible_block}{reg_block}{vat_block}

Haftung für Inhalte:
Als Diensteanbieter sind wir gemäß den gesetzlichen Vorgaben für eigene Inhalte auf diesen Seiten verantwortlich. Für die Inhalte von Verlinkungen übernehmen wir keine Gewähr; zum Zeitpunkt der Verlinkung waren keine rechtswidrigen Inhalte erkennbar.

Hinweis zur KI-Generierung:
Ausgaben von KI-Modellen (Text, Bild, Video, Audio) können fehlerhaft oder unzutreffend sein und stellen keine Rechts-, Medizin- oder Finanzberatung dar.

Stand: Dieses Impressum bezieht sich auf den Telegram-Bot und die zugehörige Web-App (Mini App), soweit angeboten.
"""

_IMPRESSUM_EN = """LEGAL NOTICE (IMPRESSUM)

Information pursuant to applicable provider-information rules (including German TMG/RStV where relevant).

Service provider / responsible party:
{legal_name}

Address:
{address}

Contact:
{email}
{phone_block}{responsible_block}{reg_block}{vat_block}

Liability for content:
We are responsible for our own content on these services as required by law. We do not endorse linked third-party content and are not liable for it unless we have positive knowledge of unlawful content.

AI-generated outputs:
Outputs from AI models may be incorrect or misleading and do not constitute legal, medical, or financial advice.

Scope: This notice refers to the Telegram bot and related web mini app, where offered.
"""

_IMPRESSUM_RU = """ПРАВОВАЯ ИНФОРМАЦИЯ (IMPRESSUM)

Сведения об операторе / ответственном лице в соответствии с применимыми правилами (включая требования Германии TMG/RStV, где применимо).

Поставщик услуг:
{legal_name}

Адрес:
{address}

Контакт:
{email}
{phone_block}{responsible_block}{reg_block}{vat_block}

Ответственность за контент:
Мы несём ответственность за собственный контент в рамках закона. Ссылки на сторонние ресурсы не означают одобрения; ответственность наступает при наличии достоверного знания о незаконном контенте.

Результаты ИИ:
Выходные данные моделей ИИ могут содержать ошибки и не являются юридической, медицинской или финансовой консультацией.

Область: бот в Telegram и связанное веб-приложение (Mini App), если предлагается.
"""

_IMPRESSUM_KK = """ЗАҢДЫ МӘЛІМЕТТЕР (IMPRESSUM)

Қызмет көрсетуші / жауапты тұлға туралы ақпарат (қолданылатын талаптарға сәйкес, соның ішінде TMG/RStV, егер қолданылса).

Қызмет көрсетуші:
{legal_name}

Мекенжай:
{address}

Байланыс:
{email}
{phone_block}{responsible_block}{reg_block}{vat_block}

Мазмұнға жауапкершілік:
Біз өз мазмұнымыз үшін заң талаптары шегінде жауаптымыз. Сыртқы сілтемелерді орналастыру оларды мақұлдау болып табылмайды.

ЖИ нәтижелері:
ЖИ модельдерінің нәтижелері қателесуі мүмкін; бұл заңдық, медициналық немесе қаржы кеңесі емес.

Қамту: Telegram боты және байланысты веб-қосымша (Mini App), егер ұсынылса.
"""


def impressum_body(lang: str) -> str:
    m = {
        "de": _IMPRESSUM_DE,
        "en": _IMPRESSUM_EN,
        "ru": _IMPRESSUM_RU,
        "kk": _IMPRESSUM_KK,
    }
    return m.get(lang, _IMPRESSUM_EN)
