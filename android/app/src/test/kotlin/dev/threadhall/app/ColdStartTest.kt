package dev.threadhall.app

import android.os.Looper
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.data.ServerConfigStore
import dev.threadhall.core.InMemoryTokenStore
import dev.threadhall.core.ThreadhallApi
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import java.util.UUID

/** A new process (new AppContainer) with persisted server + tokens resumes the session; after
 *  server-side revocation it falls back to signed-out instead of showing stale identity. */
@RunWith(AndroidJUnit4::class)
@Config(application = UiTestApp::class, sdk = [36])
class ColdStartTest {
    private val base = System.getenv("LIVE_BASE_URL").orEmpty()

    private fun pumpUntil(timeoutMs: Long = 15_000, cond: () -> Boolean) {
        val end = System.currentTimeMillis() + timeoutMs
        while (!cond() && System.currentTimeMillis() < end) {
            shadowOf(Looper.getMainLooper()).idle()
            Thread.sleep(20)
        }
    }

    @Test fun containerRestoresAndDropsSessions() {
        assumeTrue("LIVE_BASE_URL not set; live test skipped", base.isNotBlank())
        val app = ApplicationProvider.getApplicationContext<UiTestApp>()
        val store = InMemoryTokenStore()
        val handle = "cold_${UUID.randomUUID().toString().take(6)}"
        val api = ThreadhallApi(base, store)
        runBlocking { api.register(handle, "cold-${UUID.randomUUID()}") }
        ServerConfigStore(app).baseUrl = api.baseUrl.toString()

        val restarted = AppContainer(app, store)
        pumpUntil { restarted.me.value != null }
        assertEquals(handle, restarted.me.value?.handle)

        // Revoke the session from "another device" (logout), then cold start again.
        runBlocking { ThreadhallApi(base, InMemoryTokenStore(store.load())).logout() }
        val afterRevoke = AppContainer(app, store)
        pumpUntil { store.load() == null }
        assertNull("revoked session must clear local tokens", store.load())
        assertNull(afterRevoke.me.value)
    }
}
