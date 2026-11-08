package pl.matka.opp.geo

import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot

/**
 * Polilinia w lokalnym rzucie równoodległościowym (metry) wokół pierwszego punktu.
 * Dla odcinków kilkunastokilometrowych błąd rzutu jest pomijalny.
 */
class Polyline(val points: List<LatLon>) {
    init {
        require(points.size >= 2) { "Polilinia musi mieć co najmniej 2 punkty" }
    }

    private val lat0 = points[0].lat
    private val lon0 = points[0].lon
    private val kx = 111_320.0 * cos(Math.toRadians(lat0))
    private val ky = 110_540.0

    private val xs = DoubleArray(points.size) { (points[it].lon - lon0) * kx }
    private val ys = DoubleArray(points.size) { (points[it].lat - lat0) * ky }
    private val cum = DoubleArray(points.size)

    val length: Double

    val minLat = points.minOf { it.lat }
    val maxLat = points.maxOf { it.lat }
    val minLon = points.minOf { it.lon }
    val maxLon = points.maxOf { it.lon }

    init {
        for (i in 1 until points.size) {
            cum[i] = cum[i - 1] + hypot(xs[i] - xs[i - 1], ys[i] - ys[i - 1])
        }
        length = cum.last()
    }

    val start: LatLon get() = points.first()
    val end: LatLon get() = points.last()

    /** Azymut pierwszego odcinka polilinii. */
    val startBearing: Double get() = segmentBearing(0)

    /**
     * Rzut punktu na polilinię.
     * @param along dystans wzdłuż polilinii od początku; ujemny przed początkiem
     *              (przedłużenie pierwszego segmentu), > length za końcem.
     * @param crossTrack odległość od polilinii w metrach.
     */
    data class Projection(val along: Double, val crossTrack: Double, val segmentBearing: Double)

    /**
     * @param hintAlong jeśli podany, szukamy tylko segmentów w okolicy tej pozycji
     *                  (chroni przed przeskokiem na inną część krętej drogi).
     */
    fun project(p: LatLon, hintAlong: Double? = null): Projection {
        val px = (p.lon - lon0) * kx
        val py = (p.lat - lat0) * ky
        var best: Projection? = null
        var bestDist = Double.MAX_VALUE
        val last = points.size - 2
        for (i in 0..last) {
            if (hintAlong != null) {
                if (cum[i + 1] < hintAlong - 300.0 || cum[i] > hintAlong + 2000.0) continue
            }
            val ax = xs[i]; val ay = ys[i]
            val dx = xs[i + 1] - ax; val dy = ys[i + 1] - ay
            val len2 = dx * dx + dy * dy
            var t = if (len2 > 0) ((px - ax) * dx + (py - ay) * dy) / len2 else 0.0
            val minT = if (i == 0) Double.NEGATIVE_INFINITY else 0.0
            val maxT = if (i == last) Double.POSITIVE_INFINITY else 1.0
            t = t.coerceIn(minT, maxT)
            val qx = ax + t * dx; val qy = ay + t * dy
            val d = hypot(px - qx, py - qy)
            if (d < bestDist) {
                bestDist = d
                best = Projection(cum[i] + t * hypot(dx, dy), d, segmentBearing(i))
            }
        }
        return best ?: if (hintAlong != null) project(p, null) else Projection(0.0, Double.MAX_VALUE, 0.0)
    }

    private fun segmentBearing(i: Int): Double {
        val dx = xs[i + 1] - xs[i]
        val dy = ys[i + 1] - ys[i]
        return (Math.toDegrees(atan2(dx, dy)) + 360.0) % 360.0
    }

    fun boxContains(p: LatLon, marginM: Double): Boolean {
        val mLat = marginM / 110_540.0
        val mLon = marginM / kx
        return p.lat >= minLat - mLat && p.lat <= maxLat + mLat &&
            p.lon >= minLon - mLon && p.lon <= maxLon + mLon
    }
}
