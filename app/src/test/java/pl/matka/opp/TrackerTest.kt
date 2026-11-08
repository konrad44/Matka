package pl.matka.opp

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import pl.matka.opp.engine.Fix
import pl.matka.opp.engine.Odcinek
import pl.matka.opp.engine.StanWyspy
import pl.matka.opp.engine.Tracker
import pl.matka.opp.engine.Zdarzenie
import pl.matka.opp.geo.LatLon
import pl.matka.opp.geo.Polyline

class TrackerTest {
    private val lat0 = 52.0
    private val lon0 = 19.0
    private fun latAt(northM: Double) = lat0 + northM / 110_540.0

    /** Prosty odcinek 5 km na północ, limit 90. */
    private val odcinek = Odcinek(
        "test-n", "Test N", "DK1", 90, 5_000.0,
        Polyline(listOf(LatLon(lat0, lon0), LatLon(latAt(2_500.0), lon0), LatLon(latAt(5_000.0), lon0))),
    )
    /** Ten sam odcinek w przeciwnym kierunku, 20 m obok (druga jezdnia). */
    private val lonOpp = lon0 + 20.0 / (111_320.0 * Math.cos(Math.toRadians(lat0)))
    private val odcinekS = Odcinek(
        "test-s", "Test S", "DK1", 90, 5_000.0,
        Polyline(listOf(LatLon(latAt(5_000.0), lonOpp), LatLon(lat0, lonOpp))),
    )

    private fun tracker() = Tracker(listOf(odcinek, odcinekS)) { 2 }

    /** Jazda na północ ze stałą prędkością, odczyt co 1 s. */
    private fun jedz(
        t: Tracker, odM: Double, doM: Double, vKmh: Double, startMs: Long = 0,
        lon: Double = lon0, onEach: (Long, List<Zdarzenie>) -> Unit = { _, _ -> },
    ): Long {
        val v = vKmh / 3.6
        var ms = startMs
        var pos = odM
        while (pos <= doM) {
            val ev = t.onFix(Fix(ms, latAt(pos), lon, v, 0.0))
            onEach(ms, ev)
            pos += v
            ms += 1000
        }
        return ms
    }

    @Test
    fun pelnyPrzejazdZeZnanymWjazdem() {
        val t = tracker()
        val ev = ArrayList<Zdarzenie>()
        var widzianaZapowiedz = false
        var widzianyNaOdcinku: StanWyspy.NaOdcinku? = null
        jedz(t, -800.0, 5_150.0, 90.0) { _, e ->
            ev.addAll(e)
            val s = t.stan
            if (s is StanWyspy.Zapowiedz) widzianaZapowiedz = true
            if (s is StanWyspy.NaOdcinku && widzianyNaOdcinku == null) widzianyNaOdcinku = s
        }
        assertTrue(widzianaZapowiedz)
        assertEquals(1, ev.count { it is Zdarzenie.Zapowiedz })
        val wjazd = ev.filterIsInstance<Zdarzenie.Wjazd>().single()
        assertFalse(wjazd.nieznany)
        assertEquals("test-n", wjazd.odcinek.id)
        val pierwszy = widzianyNaOdcinku!!
        assertEquals(88, pierwszy.dozwolonaKmh)
        val zjazd = ev.filterIsInstance<Zdarzenie.Zjazd>().single()
        assertEquals(90, zjazd.sredniaKmh)
        assertTrue(t.stan is StanWyspy.Podsumowanie)
        // 90 > 88 -> w trakcie musiało się pojawić ostrzeżenie
        assertTrue(ev.any { it is Zdarzenie.ZaSzybko })
    }

    @Test
    fun wolnaJazdaDajeWartoscPowyzejLimitu() {
        val t = tracker()
        jedz(t, -100.0, 2_500.0, 60.0)
        val s = t.stan as StanWyspy.NaOdcinku
        assertTrue(s.dozwolonaKmh!! > 90)
        assertEquals(pl.matka.opp.engine.Kolor.NIEBIESKI, s.kolor)
        assertEquals(0.5f, s.postep, 0.02f)
    }

    @Test
    fun nieznanyWjazdPokazujeSamLimit() {
        val t = tracker()
        val ev = ArrayList<Zdarzenie>()
        jedz(t, 1_000.0, 1_200.0, 90.0) { _, e -> ev.addAll(e) }
        assertTrue(ev.filterIsInstance<Zdarzenie.Wjazd>().single().nieznany)
        val s = t.stan as StanWyspy.NaOdcinku
        assertTrue(s.nieznanyWjazd)
        assertEquals(null, s.dozwolonaKmh)
    }

    @Test
    fun przeciwnyKierunekNieJestWykrywanyJakoTenOdcinek() {
        val t = tracker()
        val ev = ArrayList<Zdarzenie>()
        // jedziemy na południe drugą jezdnią
        val v = 25.0
        var ms = 0L
        var pos = 5_800.0
        while (pos > -300) {
            ev.addAll(t.onFix(Fix(ms, latAt(pos), lonOpp, v, 180.0)))
            pos -= v; ms += 1000
        }
        val wjazdy = ev.filterIsInstance<Zdarzenie.Wjazd>()
        assertEquals(1, wjazdy.size)
        assertEquals("test-s", wjazdy[0].odcinek.id)
        assertFalse(wjazdy[0].nieznany)
    }

    @Test
    fun utrataGpsSzacujePozycje() {
        val t = tracker()
        val koniecMs = jedz(t, -100.0, 1_000.0, 90.0)
        val przed = (t.stan as StanWyspy.NaOdcinku).postep
        t.onTick(koniecMs + 10_000)
        val s = t.stan as StanWyspy.NaOdcinku
        assertTrue(s.szacowane)
        assertEquals(pl.matka.opp.engine.Kolor.SZARY, s.kolor)
        assertTrue(s.postep > przed + 0.04f)
    }

    @Test
    fun zjazdZTrasyKonczyOdcinekBezPodsumowania() {
        val t = tracker()
        var ms = jedz(t, -100.0, 1_000.0, 90.0)
        val ev = ArrayList<Zdarzenie>()
        // skręcamy 300 m w bok i stoimy tam 25 s
        val lonBok = lon0 + 300.0 / (111_320.0 * Math.cos(Math.toRadians(lat0)))
        repeat(25) {
            ev.addAll(t.onFix(Fix(ms, latAt(1_000.0), lonBok, 15.0, 90.0)))
            ms += 1000
        }
        val z = ev.filterIsInstance<Zdarzenie.Zjazd>().single()
        assertTrue(z.zTrasy)
        assertTrue(t.stan is StanWyspy.Czuwanie)
    }

    @Test
    fun podsumowanieZnikaPo10s() {
        val t = tracker()
        val ms = jedz(t, -100.0, 5_100.0, 90.0)
        assertTrue(t.stan is StanWyspy.Podsumowanie)
        t.onFix(Fix(ms + 11_000, latAt(5_400.0), lon0, 25.0, 0.0))
        assertTrue(t.stan is StanWyspy.Czuwanie)
    }
}
