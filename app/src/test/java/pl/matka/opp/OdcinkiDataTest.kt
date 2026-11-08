package pl.matka.opp

import org.junit.Assert.assertTrue
import org.junit.Test
import pl.matka.opp.engine.OdcinkiParser
import java.io.File

class OdcinkiDataTest {
    @Test
    fun plikDanychJestPoprawny() {
        val f = listOf(File("../data/odcinki.json"), File("data/odcinki.json")).first { it.exists() }
        val d = OdcinkiParser.parse(f.readText())
        assertTrue(d.odcinki.size > 100)
        for (o in d.odcinki) {
            assertTrue(o.id, o.limit in 20..140)
            assertTrue(o.id, o.dlugoscM > 100)
            // długość trasy zgodna z oficjalną z dokładnością do 10%
            assertTrue(o.id, kotlin.math.abs(o.trasa.length - o.dlugoscM) / o.dlugoscM < 0.1)
        }
    }
}
