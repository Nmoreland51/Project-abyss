package dev.threadhall.app

import android.app.Application
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.data.KeystoreTokenStore
import dev.threadhall.core.TokenStore

open class ThreadhallApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this, createTokenStore())
    }

    /** Overridden in JVM UI tests (Robolectric has no Android Keystore). */
    protected open fun createTokenStore(): TokenStore = KeystoreTokenStore(this)
}
