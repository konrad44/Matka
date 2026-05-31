# Mapa Gdyni — SKM, pole dance i mieszkania > 80 m²

Interaktywna strona na Google Maps pokazująca w Gdyni:

- 🚆 **Przystanki SKM** (warstwa) — z kołem zasięgu **1,5 km** blednącym ku krawędzi
- 💃 **Studia pole dance** (warstwa) — z kołem zasięgu i **linkiem**
- 🏠 **Oferty sprzedaży mieszkań > 80 m²** (warstwa) — tylko te **w zasięgu 1,5 km od dowolnego przystanku SKM**, każda z **linkiem do oferty**

Każda grupa jest osobną, przełączalną warstwą (panel po lewej).

## Uruchomienie

Google Maps wymaga klucza API, więc:

1. Wejdź na [Google Cloud Console](https://console.cloud.google.com/google/maps-apis) i włącz **Maps JavaScript API**, utwórz klucz.
2. Otwórz `index.html` (najlepiej przez serwer lokalny, np. `python3 -m http.server`).
3. Wklej klucz w okienku startowym → **Pokaż mapę**. Klucz zapisuje się tylko w `localStorage` przeglądarki.

```bash
python3 -m http.server 8000
# otwórz http://localhost:8000
```

## Dane

| Warstwa | Źródło | Status |
|---|---|---|
| Przystanki SKM | `js/data.js → PRZYSTANKI_SKM` | realne stacje SKM w Gdyni (współrzędne ~ dokładne) |
| Studia pole dance | `js/data.js → STUDIA_POLEDANCE` | **przykładowe** — zweryfikuj adresy/linki |
| Mieszkania | `js/data.js → OFERTY_MIESZKAN` | **przykładowe** — podmień na realne oferty |

### Dlaczego mieszkania są przykładowe?

Aktualnych ofert nie da się pobierać na żywo z portali (Otodom/OLX blokują scraping, a dane szybko się dezaktualizują). Dlatego:

- w `OFERTY_MIESZKAN` są edytowalne wpisy (wystarczy podać `lat`, `lng`, `area`, `cena`, `link`),
- przycisk **„Aktualne oferty na Otodom ↗”** prowadzi do wyszukiwarki Otodom z filtrem Gdynia + powierzchnia ≥ 80 m².

Filtry **> 80 m²** oraz **≤ 1,5 km od SKM** liczone są w przeglądarce (`js/app.js`, haversine) — oferty niespełniające warunków są automatycznie pomijane.

## Struktura

```
index.html      # strona + ekran klucza API + panel warstw
css/styles.css  # style
js/data.js      # dane (przystanki, studia, mieszkania) — to edytujesz
js/app.js       # logika mapy, warstwy, koła dystansu, filtr
```

## Jak dodać mieszkanie

W `js/data.js`:

```js
{ tytul: "Mieszkanie 92 m², Działki Leśne", lat: 54.5210, lng: 18.5350, area: 92, cena: "1 150 000 zł", link: "https://www.otodom.pl/pl/oferta/..." }
```

Jeśli będzie dalej niż 1,5 km od najbliższego SKM lub ≤ 80 m², nie pojawi się na mapie (zgodnie z założeniem).
