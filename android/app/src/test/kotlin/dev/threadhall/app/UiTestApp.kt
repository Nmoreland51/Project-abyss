package dev.threadhall.app

import dev.threadhall.core.InMemoryTokenStore
import dev.threadhall.core.TokenStore

/** Robolectric has no Android Keystore; JVM UI tests keep tokens in memory instead. */
class UiTestApp : ThreadhallApp() {
    val tokens = InMemoryTokenStore()
    override fun createTokenStore(): TokenStore = tokens
}
