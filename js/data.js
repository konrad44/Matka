// ============================================================================
//  DANE MAPY — Gdynia
// ----------------------------------------------------------------------------
//  - PRZYSTANKI_SKM : realne stacje SKM w granicach Gdyni (współrzędne ~ dokładne)
//  - STUDIA_POLEDANCE : lista studiów pole dance (zweryfikuj/uzupełnij linki i adresy)
//  - OFERTY_MIESZKAN : oferty sprzedaży mieszkań > 80 m2 (dane przykładowe/edytowalne)
//
//  Filtr 1,5 km od przystanku SKM oraz warunek > 80 m2 liczone są w app.js.
//  Żeby dodać ofertę: dopisz obiekt do OFERTY_MIESZKAN z polami lat,lng,area,link.
// ============================================================================

// --- Przystanki SKM w Gdyni (linia SKM Trójmiasto) -------------------------
const PRZYSTANKI_SKM = [
  { nazwa: "Gdynia Cisowa",                    lat: 54.5639, lng: 18.4869 },
  { nazwa: "Gdynia Chylonia",                  lat: 54.5563, lng: 18.5049 },
  { nazwa: "Gdynia Leszczynki",                lat: 54.5431, lng: 18.5256 },
  { nazwa: "Gdynia Grabówek",                  lat: 54.5349, lng: 18.5360 },
  { nazwa: "Gdynia Stocznia (Uniw. Morski)",   lat: 54.5268, lng: 18.5432 },
  { nazwa: "Gdynia Główna",                    lat: 54.5189, lng: 18.5306 },
  { nazwa: "Gdynia Wzg. Św. Maksymiliana",     lat: 54.5072, lng: 18.5404 },
  { nazwa: "Gdynia Redłowo",                   lat: 54.4961, lng: 18.5521 },
  { nazwa: "Gdynia Orłowo",                    lat: 54.4836, lng: 18.5618 },
];

// --- Studia pole dance ------------------------------------------------------
// UWAGA: współrzędne przybliżone do okolicy. Zweryfikuj adres/link przed użyciem.
const STUDIA_POLEDANCE = [
  {
    nazwa: "Pole Dance Studio Gdynia (przykład – Śródmieście)",
    lat: 54.5175, lng: 18.5375,
    link: "https://www.google.com/maps/search/pole+dance+gdynia+%C5%9Br%C3%B3dmie%C5%9Bcie",
  },
  {
    nazwa: "Studio Pole / Aerial (przykład – Wzg. Św. Maksymiliana)",
    lat: 54.5085, lng: 18.5360,
    link: "https://www.google.com/maps/search/pole+dance+gdynia",
  },
  {
    nazwa: "Pole Fitness (przykład – Chylonia)",
    lat: 54.5550, lng: 18.5100,
    link: "https://www.google.com/maps/search/pole+fitness+gdynia+chylonia",
  },
  {
    nazwa: "Studio Tańca na rurze (przykład – Redłowo)",
    lat: 54.4975, lng: 18.5490,
    link: "https://www.google.com/maps/search/pole+dance+gdynia+red%C5%82owo",
  },
];

// --- Oferty sprzedaży mieszkań > 80 m2 -------------------------------------
// Dane przykładowe. `link` prowadzi do oferty lub do wyszukiwarki Otodom.
// Mieszkania dalej niż 1,5 km od dowolnego przystanku SKM zostaną odfiltrowane.
const OFERTY_MIESZKAN = [
  { tytul: "Mieszkanie 3-pok. 86 m², Śródmieście",  lat: 54.5160, lng: 18.5340, area: 86,  cena: "1 250 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Apartament 4-pok. 102 m², Wzgórze",     lat: 54.5090, lng: 18.5390, area: 102, cena: "1 690 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Mieszkanie 90 m² z tarasem, Redłowo",   lat: 54.4945, lng: 18.5495, area: 90,  cena: "1 420 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Apartament 95 m² blisko morza, Orłowo", lat: 54.4850, lng: 18.5590, area: 95,  cena: "2 100 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Mieszkanie 4-pok. 88 m², Grabówek",     lat: 54.5360, lng: 18.5340, area: 88,  cena: "980 000 zł",   link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Mieszkanie 110 m², Chylonia",           lat: 54.5575, lng: 18.5070, area: 110, cena: "1 050 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Apartament 84 m², Leszczynki",          lat: 54.5420, lng: 18.5240, area: 84,  cena: "899 000 zł",   link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Mieszkanie 120 m², Mały Kack (daleko)", lat: 54.4700, lng: 18.5300, area: 120, cena: "1 600 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
  { tytul: "Dom-mieszkanie 130 m², Wielki Kack (daleko)", lat: 54.4600, lng: 18.4900, area: 130, cena: "1 350 000 zł", link: "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80" },
];

// Deep-link do aktualnych ofert (Otodom, Gdynia, > 80 m²)
const OTODOM_LIVE_SEARCH =
  "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdynia/gdynia/gdynia?areaMin=80&by=PRICE&direction=ASC";
