import pytest

from regradar.adapters.dip.web_url import procedure_web_url


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        (
            # Truncated after ten words, umlauts kept and percent-encoded.
            "Lage der christlichen Minderheit im Jemen im Kontext des "
            "langjährigen Bürgerkriegs und der dschihadistischen Bedrohung",
            "lage-der-christlichen-minderheit-im-jemen-im-kontext-des-"
            "langj%C3%A4hrigen",
        ),
        (
            "Gesetz zur Umsetzung der Richtlinie (EU) 2022/2556 – DORA",
            "gesetz-zur-umsetzung-der-richtlinie-eu-2022-2556-dora",
        ),
        ("  Straße  /  Maß ", "stra%C3%9Fe-ma%C3%9F"),
    ],
)
def test_procedure_url_matches_dip_frontend(title: str, slug: str) -> None:
    assert procedure_web_url(title, "338726") == (
        f"https://dip.bundestag.de/vorgang/{slug}/338726"
    )
