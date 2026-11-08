package pl.matka.opp.android

import android.app.NotificationManager
import android.app.PendingIntent
import android.bluetooth.BluetoothDevice
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import pl.matka.opp.R

/** Start/stop usługi po połączeniu/rozłączeniu z Bluetoothem auta. */
class BluetoothReceiver : BroadcastReceiver() {
    override fun onReceive(ctx: Context, intent: Intent) {
        val dev: BluetoothDevice? = if (Build.VERSION.SDK_INT >= 33) {
            intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
        } else {
            @Suppress("DEPRECATION") intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
        }
        val adres = dev?.address ?: return
        if (adres !in Prefs(ctx).urzadzenia) return
        when (intent.action) {
            BluetoothDevice.ACTION_ACL_CONNECTED -> try {
                TrackingService.wyslij(ctx, TrackingService.ACTION_BT_POLACZONO)
            } catch (e: Exception) {
                // Android może zablokować start z tła (np. przy optymalizacji baterii) – dajemy przycisk.
                Log.w("BluetoothReceiver", "Start z tła zablokowany", e)
                powiadomOStarcie(ctx)
            }
            BluetoothDevice.ACTION_ACL_DISCONNECTED ->
                TrackingService.wyslij(ctx, TrackingService.ACTION_BT_ROZLACZONO)
        }
    }

    private fun powiadomOStarcie(ctx: Context) {
        TrackingService.utworzKanal(ctx)
        val pi = PendingIntent.getActivity(
            ctx, 2,
            Intent(ctx, MainActivity::class.java).setAction(MainActivity.ACTION_URUCHOM)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val n = NotificationCompat.Builder(ctx, TrackingService.KANAL)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle("Połączono z autem")
            .setContentText("Dotknij, aby uruchomić odcinkowy pomiar")
            .setContentIntent(pi)
            .setAutoCancel(true)
            .build()
        runCatching { ctx.getSystemService(NotificationManager::class.java).notify(2, n) }
    }
}
