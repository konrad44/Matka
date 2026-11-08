package pl.matka.opp

import org.junit.Assert.assertTrue
import org.junit.Test
import pl.matka.opp.engine.Fix
import pl.matka.opp.engine.Odcinek
import pl.matka.opp.engine.OdcinkiParser
import pl.matka.opp.engine.Tracker
import pl.matka.opp.engine.Zdarzenie
import pl.matka.opp.geo.Geo
import pl.matka.opp.geo.LatLon
import java.io.File

/** Symulacja przejazdu każdego odcinka z pliku danych po jego własnej trasie. */
class PrawdziweOdcinkiTest {
    private val dane = OdcinkiParser.parse(
        listOf(File("../data/odcinki.json"), File("data/odcinki.json")).first { it.exists() }.readText()
    )

    /** Punkty co [krokM] wzdłuż trasy, z 400 m dobiegiem przed startem i 100 m za końcem. */
    private fun przejazd(o: Odcinek, krokM: Double): List<Pair<LatLon, Double>> {
        val pts = o.trasa.points
        val out = ArrayList<Pair<LatLon, Double>>()
        val b0 = Geo.bearing(pts[0], pts[1])
        fun przesun(p: LatLon, brg: Double, m: Double): LatLon {
            val r = Math.toRadians(brg)
            return LatLon(p.lat + m * Math.cos(r) / 110_540.0, p.lon + m * Math.sin(r) / (111_320.0 * Math.cos(Math.toRadians(p.lat))))
        }
        var m = -Math.ceil(400.0 / krokM) * krokM
        while (m < 0) { out.add(przesun(pts[0], b0, m) to b0); m += krokM }
        var reszta = 0.0
        for (i in 0 until pts.size - 1) {
            val a = pts[i]; val b = pts[i + 1]
            val len = Geo.distance(a, b); val brg = Geo.bearing(a, b)
            var s = reszta
            while (s < len) { out.add(przesun(a, brg, s) to brg); s += krokM }
            reszta = s - len
        }
        val bl = Geo.bearing(pts[pts.size - 2], pts.last())
        m = reszta
        while (m <= 100) { out.add(przesun(pts.last(), bl, m) to bl); m += krokM }
        return out
    }

    @Test
    fun kazdyOdcinekWykrytyOdWjazduDoZjazdu() {
        val bledy = ArrayList<String>()
        for (o in dane.odcinki) {
            val t = Tracker(dane.odcinki) { 0 }
            val v = o.limit / 3.6
            val ev = ArrayList<Zdarzenie>()
            var ms = 0L
            for ((p, brg) in przejazd(o, v)) {
                ev.addAll(t.onFix(Fix(ms, p.lat, p.lon, v, brg)))
                ms += 1000
            }
            val wjazd = ev.filterIsInstance<Zdarzenie.Wjazd>().firstOrNull()
            val zjazd = ev.filterIsInstance<Zdarzenie.Zjazd>().firstOrNull()
            when {
                wjazd == null -> bledy.add("${o.id}: brak wjazdu")
                wjazd.odcinek.id != o.id -> bledy.add("${o.id}: wykryto ${wjazd.odcinek.id}")
                wjazd.nieznany -> bledy.add("${o.id}: nieznany wjazd")
                zjazd == null -> bledy.add("${o.id}: brak zjazdu")
                zjazd.zTrasy -> bledy.add("${o.id}: zjazd z trasy")
                zjazd.sredniaKmh == null || kotlin.math.abs(zjazd.sredniaKmh!! - o.limit) > o.limit * 0.08 ->
                    bledy.add("${o.id}: średnia ${zjazd.sredniaKmh} przy limicie ${o.limit}")
            }
        }
        println("Błędy: ${bledy.size}/${dane.odcinki.size}\n" + bledy.joinToString("\n"))
        assertTrue(bledy.joinToString("\n"), bledy.isEmpty())
    }
}
