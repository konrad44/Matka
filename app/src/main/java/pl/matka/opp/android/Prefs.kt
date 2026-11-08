package pl.matka.opp.android

import android.content.Context

enum class Tryb { SYGNAL, GLOS, CICHY }

class Prefs(ctx: Context) {
    private val sp = ctx.getSharedPreferences("matka", Context.MODE_PRIVATE)

    var zapasKmh: Int
        get() = sp.getInt("zapas", 2)
        set(v) = sp.edit().putInt("zapas", v.coerceIn(0, 20)).apply()

    var tryb: Tryb
        get() = runCatching { Tryb.valueOf(sp.getString("tryb", Tryb.SYGNAL.name)!!) }.getOrDefault(Tryb.SYGNAL)
        set(v) = sp.edit().putString("tryb", v.name).apply()

    /** Adresy MAC urządzeń Bluetooth auta. */
    var urzadzenia: Set<String>
        get() = sp.getStringSet("bt", emptySet())!!.toSet()
        set(v) = sp.edit().putStringSet("bt", v).apply()

    var wyspaX: Int
        get() = sp.getInt("wx", 24)
        set(v) = sp.edit().putInt("wx", v).apply()

    var wyspaY: Int
        get() = sp.getInt("wy", 300)
        set(v) = sp.edit().putInt("wy", v).apply()

    /** Kiedy ostatnio sprawdzano aktualizację odcinków (System.currentTimeMillis). */
    var ostatnieSprawdzenie: Long
        get() = sp.getLong("upd", 0L)
        set(v) = sp.edit().putLong("upd", v).apply()
}
