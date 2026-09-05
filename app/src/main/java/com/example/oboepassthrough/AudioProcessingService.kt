package com.example.oboepassthrough

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioManager
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat

/**
 * Android Foreground Service maintaining continuous low-latency native Oboe audio passthrough.
 * Integrates acoustic safety receiver to auto-mute if headphones are disconnected.
 */
class AudioProcessingService : Service() {

    private val tag = "OboeAudioService"

    // Broadcast receiver to guard against loudspeaker acoustic feedback
    private val noisyReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == AudioManager.ACTION_AUDIO_BECOMING_NOISY) {
                Log.w(tag, "Headphones disconnected (ACTION_AUDIO_BECOMING_NOISY). Stopping passthrough to prevent acoustic feedback.")
                stopSelf()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()

        val filter = IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY)
        registerReceiver(noisyReceiver, filter)
        Log.i(tag, "Service created with acoustic feedback protection active.")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)

        try {
            startPassthrough()
            Log.i(tag, "Native startPassthrough() invoked successfully.")
        } catch (e: UnsatisfiedLinkError) {
            Log.e(tag, "Native library missing: ${e.message}")
            stopSelf()
        } catch (e: Exception) {
            Log.e(tag, "Error starting native audio: ${e.message}")
            stopSelf()
        }

        return START_STICKY
    }

    override fun onDestroy() {
        try {
            unregisterReceiver(noisyReceiver)
        } catch (e: Exception) {
            Log.w(tag, "Receiver already unregistered: ${e.message}")
        }

        try {
            stopPassthrough()
            Log.i(tag, "Native stopPassthrough() invoked successfully.")
        } catch (e: Exception) {
            Log.e(tag, "Error stopping native audio: ${e.message}")
        }

        super.onDestroy()
        Log.i(tag, "Service destroyed safely.")
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Ultra-Low Latency Audio Stream",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors real-time microphone to earphone audio passthrough."
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Oboe Passthrough Active")
            .setContentText("Ultra-low latency audio processing running in background.")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setOngoing(true)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    // --- JNI Functions ---
    private external fun startPassthrough()
    private external fun stopPassthrough()

    companion object {
        const val CHANNEL_ID = "AudioProcessingServiceChannel"
        const val NOTIFICATION_ID = 2001

        init {
            try {
                System.loadLibrary("native-lib")
                Log.i("OboeAudioService", "native-lib loaded successfully.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("OboeAudioService", "Failed to load native-lib: ${e.message}")
            }
        }
    }
}
