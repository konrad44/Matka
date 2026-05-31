// ============================================================================
//  Mapa Gdyni: przystanki SKM + studia pole dance + oferty mieszkań > 80 m²
//  Warstwy przełączalne, koła dystansu blednące ku krawędzi.
// ============================================================================

const PROMIEN_SKM_M    = 1500; // koło dystansu wokół przystanku SKM (i filtr mieszkań)
const PROMIEN_STUDIO_M = 800;  // koło dystansu wokół studia
const KLUCZ_LS         = "gdynia_gmaps_key";

let map;
const warstwy = {
  skm:        { obiekty: [], widoczna: true },
  studia:     { obiekty: [], widoczna: true },
  mieszkania: { obiekty: [], widoczna: true },
};

// --- Custom overlay: koło z gradientem blednącym ku krawędzi ----------------
// Definiowane dopiero po załadowaniu Google Maps (google.maps musi istnieć).
let KoloBlednace;
function zdefiniujKoloBlednace() {
  KoloBlednace = class extends google.maps.OverlayView {
    constructor(center, radiusM, kolorRGB) {
      super();
      this.center = new google.maps.LatLng(center.lat, center.lng);
      this.radiusM = radiusM;
      this.kolor = kolorRGB; // "R,G,B"
      this.div = null;
    }
    onAdd() {
      const div = document.createElement("div");
      div.style.position = "absolute";
      div.style.borderRadius = "50%";
      div.style.pointerEvents = "none";
      div.style.background =
        `radial-gradient(circle, rgba(${this.kolor},0.45) 0%, ` +
        `rgba(${this.kolor},0.22) 45%, rgba(${this.kolor},0) 78%)`;
      this.div = div;
      this.getPanes().overlayLayer.appendChild(div);
    }
    draw() {
      if (!this.div) return;
      const proj = this.getProjection();
      if (!proj) return;
      const centerPx = proj.fromLatLngToDivPixel(this.center);
      const edge = google.maps.geometry.spherical.computeOffset(this.center, this.radiusM, 90);
      const edgePx = proj.fromLatLngToDivPixel(edge);
      const rpx = Math.abs(edgePx.x - centerPx.x);
      const s = this.div.style;
      s.width = `${rpx * 2}px`;
      s.height = `${rpx * 2}px`;
      s.left = `${centerPx.x - rpx}px`;
      s.top = `${centerPx.y - rpx}px`;
    }
    onRemove() {
      if (this.div && this.div.parentNode) this.div.parentNode.removeChild(this.div);
      this.div = null;
    }
    setWidoczna(v) {
      if (this.div) this.div.style.display = v ? "block" : "none";
    }
  };
}

// --- Ikona markera (kropka SVG) --------------------------------------------
function ikona(kolor) {
  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale: 8,
    fillColor: kolor,
    fillOpacity: 1,
    strokeColor: "#ffffff",
    strokeWeight: 2,
  };
}

// --- Haversine: dystans w metrach ------------------------------------------
function dystansM(a, b) {
  const R = 6371000, toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat), dLng = toRad(b.lng - a.lng);
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function najblizszyPrzystanek(p) {
  let min = Infinity, naz = null;
  for (const s of PRZYSTANKI_SKM) {
    const d = dystansM(p, s);
    if (d < min) { min = d; naz = s.nazwa; }
  }
  return { dystans: min, nazwa: naz };
}

// --- Budowa warstw ----------------------------------------------------------
function dodajPrzystanki() {
  const okno = new google.maps.InfoWindow();
  for (const s of PRZYSTANKI_SKM) {
    const marker = new google.maps.Marker({
      position: { lat: s.lat, lng: s.lng },
      map, icon: ikona("#1e88e5"), title: s.nazwa, zIndex: 30,
    });
    const kolo = new KoloBlednace(s, PROMIEN_SKM_M, "30,136,229");
    kolo.setMap(map);
    marker.addListener("click", () => {
      okno.setContent(
        `<div class="iw"><strong>🚆 ${s.nazwa}</strong><br>` +
        `Przystanek SKM<br><small>Koło = zasięg 1,5 km</small></div>`
      );
      okno.open(map, marker);
    });
    warstwy.skm.obiekty.push({ marker, kolo });
  }
}

function dodajStudia() {
  const okno = new google.maps.InfoWindow();
  for (const s of STUDIA_POLEDANCE) {
    const marker = new google.maps.Marker({
      position: { lat: s.lat, lng: s.lng },
      map, icon: ikona("#e91e63"), title: s.nazwa, zIndex: 25,
    });
    const kolo = new KoloBlednace(s, PROMIEN_STUDIO_M, "233,30,99");
    kolo.setMap(map);
    const nz = najblizszyPrzystanek(s);
    marker.addListener("click", () => {
      okno.setContent(
        `<div class="iw"><strong>💃 ${s.nazwa}</strong><br>` +
        `Studio pole dance<br>` +
        `Najbliższy SKM: ${nz.nazwa} (${(nz.dystans/1000).toFixed(2)} km)<br>` +
        `<a href="${s.link}" target="_blank" rel="noopener">Otwórz link ↗</a></div>`
      );
      okno.open(map, marker);
    });
    warstwy.studia.obiekty.push({ marker, kolo });
  }
}

function dodajMieszkania() {
  const okno = new google.maps.InfoWindow();
  let pokazane = 0;
  for (const m of OFERTY_MIESZKAN) {
    if (m.area <= 80) continue;                       // warunek > 80 m²
    const nz = najblizszyPrzystanek(m);
    if (nz.dystans > PROMIEN_SKM_M) continue;          // warunek <= 1,5 km od SKM
    pokazane++;
    const marker = new google.maps.Marker({
      position: { lat: m.lat, lng: m.lng },
      map, icon: ikona("#43a047"), title: m.tytul, zIndex: 20,
    });
    marker.addListener("click", () => {
      okno.setContent(
        `<div class="iw"><strong>🏠 ${m.tytul}</strong><br>` +
        `Powierzchnia: <b>${m.area} m²</b><br>` +
        `Cena: ${m.cena || "—"}<br>` +
        `SKM ${nz.nazwa}: ${(nz.dystans/1000).toFixed(2)} km<br>` +
        `<a href="${m.link}" target="_blank" rel="noopener">Zobacz ofertę ↗</a></div>`
      );
      okno.open(map, marker);
    });
    warstwy.mieszkania.obiekty.push({ marker, kolo: null });
  }
  return pokazane;
}

// --- Przełączanie widoczności warstw ---------------------------------------
function ustawWarstwe(klucz, widoczna) {
  warstwy[klucz].widoczna = widoczna;
  for (const o of warstwy[klucz].obiekty) {
    o.marker.setMap(widoczna ? map : null);
    if (o.kolo) o.kolo.setWidoczna(widoczna);
  }
}

// --- Inicjalizacja mapy -----------------------------------------------------
function initMapa() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 54.5189, lng: 18.5306 }, // Gdynia Główna
    zoom: 13,
    mapTypeControl: true,
    streetViewControl: false,
    fullscreenControl: true,
  });

  zdefiniujKoloBlednace();
  dodajPrzystanki();
  dodajStudia();
  const liczbaMieszkan = dodajMieszkania();

  document.getElementById("cb-skm").addEventListener("change", (e) => ustawWarstwe("skm", e.target.checked));
  document.getElementById("cb-studia").addEventListener("change", (e) => ustawWarstwe("studia", e.target.checked));
  document.getElementById("cb-mieszkania").addEventListener("change", (e) => ustawWarstwe("mieszkania", e.target.checked));

  document.getElementById("licznik-mieszkan").textContent = liczbaMieszkan;
  document.getElementById("otodom-link").href = OTODOM_LIVE_SEARCH;
  document.getElementById("panel").classList.remove("ukryty");
}

// --- Ładowanie Google Maps API z kluczem użytkownika ------------------------
function zaladujMape(klucz) {
  document.getElementById("ekran-klucza").style.display = "none";
  const s = document.createElement("script");
  s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(klucz)}` +
          `&libraries=geometry&callback=initMapa&language=pl&region=PL`;
  s.async = true;
  s.onerror = () => {
    alert("Nie udało się załadować Google Maps. Sprawdź klucz API i połączenie.");
    document.getElementById("ekran-klucza").style.display = "flex";
  };
  document.head.appendChild(s);
}

window.initMapa = initMapa;

document.addEventListener("DOMContentLoaded", () => {
  const zapisany = localStorage.getItem(KLUCZ_LS);
  const input = document.getElementById("input-klucz");
  if (zapisany) input.value = zapisany;

  document.getElementById("btn-klucz").addEventListener("click", () => {
    const klucz = input.value.trim();
    if (!klucz) { alert("Wklej klucz Google Maps API."); return; }
    if (document.getElementById("zapamietaj").checked) localStorage.setItem(KLUCZ_LS, klucz);
    zaladujMape(klucz);
  });
});
