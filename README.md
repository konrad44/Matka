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
| Studia pole dance | `js/data.js → STUDIA_POLEDANCE` | **realne** — nazwy/adresy/strony zweryfikowane w sieci (maj 2026), współrzędne przybliżone z adresu |
| Mieszkania | `js/data.js → OFERTY_MIESZKAN` | **przykładowe** — scraping ofert się nie udał (patrz niżej) |

### Dlaczego mieszkania są przykładowe?

Próba scrapowania aktualnych ofert się nie powiodła: Otodom, gethome, nieruchomosci-online, domiporta i ogłoszenia trojmiasto.pl zwracają **HTTP 403** dla automatycznych zapytań (ochrona anty-bot), a środowisko ma allowlistę sieci blokującą bezpośrednie `curl`/geokodery (Nominatim, Photon). Dostępne były tylko zagregowane statystyki, bez pojedynczych ofert ze współrzędnymi i linkami. Dlatego:

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

W `js/data.js` — możesz podać **współrzędne** albo **sam adres** (zostanie zgeokodowany przez Google):

```js
// z współrzędnymi:
{ tytul: "Mieszkanie 92 m², Działki Leśne", lat: 54.5210, lng: 18.5350, area: 92, cena: "1 150 000 zł", link: "https://www.otodom.pl/pl/oferta/..." }
// albo z samym adresem (aplikacja policzy lat/lng):
{ tytul: "Mieszkanie 92 m²", adres: "ul. Świętojańska 50", area: 92, cena: "1 150 000 zł", link: "https://..." }
```

Jeśli będzie dalej niż 1,5 km od najbliższego SKM lub ≤ 80 m², nie pojawi się na mapie (zgodnie z założeniem).

## Skąd wziąć dane ofert (skoro scraping nie działa)

Scraping nie działa z dwóch powodów: (1) **proxy sieciowe środowiska** przepuszcza tylko GitHub — Otodom/OLX/gethome dostają `403 host_not_allowed` zanim w ogóle dotrą do serwera, więc headless browser (Playwright) też nic nie da; (2) nawet przez zewnętrzny fetch portale mają ochronę anty-bot (403). Realne drogi:

### Opcja A — oficjalne API / proxy do scrapingu (najwięcej roboty, najczystsze dane)
Portale nie mają publicznego API, więc używa się usług proxy renderujących stronę i omijających anty-bota:
- **ScraperAPI** (scraperapi.com) lub **ZenRows** (zenrows.com) — rejestrujesz się, dostajesz `API_KEY`, wołasz `https://api.scraperapi.com/?api_key=KEY&url=<URL_OTODOM>&render=true` i parsujesz HTML.
- **Apify** (apify.com) — gotowe „aktory" do Otodom/OLX; odpalasz aktora, dostajesz JSON z ofertami (tytuł, m², cena, link, czasem geo). Klucz w Apify Console → *Settings → Integrations → API token*.
- Z każdego z nich wyciągasz: tytuł, powierzchnię, cenę, link, adres → wrzucasz do `OFERTY_MIESZKAN` (adres wystarczy, resztę policzy geokoder).

### Opcja B — klucz Google Geocoding (najszybsze przy ręcznym wklejaniu)
Już zaimplementowane. Wystarczy że w ofercie podasz `adres` — aplikacja sama policzy współrzędne.
1. [Google Cloud Console](https://console.cloud.google.com/google/maps-apis) → włącz **Geocoding API** (oprócz Maps JavaScript API) na tym samym kluczu.
2. Kopiujesz oferty z Otodom ręcznie (adres + m² + cena + link) do `OFERTY_MIESZKAN`.

### Opcja C — odblokowanie sieci w środowisku (żeby scraping zadziałał w sesji)
Sieć tej sesji jest ograniczona polityką środowiska. Żeby Claude mógł sięgnąć po portale, trzeba zmienić politykę sieciową środowiska Claude Code on the web (allowlista domen) — instrukcja: <https://code.claude.com/docs/en/claude-code-on-the-web>. Po dodaniu domen (np. `otodom.pl`) do allowlisty mogę spróbować pobrać oferty przez Playwright.
