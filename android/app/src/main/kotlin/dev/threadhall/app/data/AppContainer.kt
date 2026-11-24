package dev.threadhall.app.data

import android.content.Context
import androidx.core.content.edit
import dev.threadhall.app.BuildConfig
import dev.threadhall.core.ApiException
import dev.threadhall.core.Me
import dev.threadhall.core.SessionEvent
import dev.threadhall.core.ThreadhallApi
import dev.threadhall.core.TokenStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers

/** The only server this client talks to is the one the user configures. No other hosts. */
class ServerConfigStore(context: Context) {
    private val prefs = context.getSharedPreferences("server", Context.MODE_PRIVATE)
    var baseUrl: String?
        get() = prefs.getString("base_url", null)
        set(value) { prefs.edit { putString("base_url", value) } }
}

/** Manual dependency container (one per process). Tests can supply their own [TokenStore]. */
class AppContainer(context: Context, private val tokenStore: TokenStore) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val serverConfig = ServerConfigStore(context)
    private val userAgent = "Threadhall-Android/${BuildConfig.VERSION_NAME}"

    private val _api = MutableStateFlow(serverConfig.baseUrl?.let { runCatching { build(it) }.getOrNull() })
    val api: StateFlow<ThreadhallApi?> = _api.asStateFlow()

    private val _me = MutableStateFlow<Me?>(null)
    val me: StateFlow<Me?> = _me.asStateFlow()

    /** Bumped after this user's own writes (post, delete, join/leave) so lists refresh. */
    private val _contentVersion = MutableStateFlow(0L)
    val contentVersion: StateFlow<Long> = _contentVersion.asStateFlow()

    fun markContentChanged() { _contentVersion.value += 1 }

    private val _messages = MutableSharedFlow<String>(extraBufferCapacity = 8)
    val messages: SharedFlow<String> = _messages.asSharedFlow()

    private var sessionWatcher: Job? = null

    init {
        _api.value?.let { watch(it); refreshMe() }
    }

    fun requireApi(): ThreadhallApi = checkNotNull(_api.value) { "No server configured" }

    /** Switching servers signs out: tokens from one server are meaningless on another. */
    fun setServer(url: String): ThreadhallApi {
        val api = build(url)
        if (serverConfig.baseUrl != api.baseUrl.toString()) {
            tokenStore.clear()
            _me.value = null
        }
        serverConfig.baseUrl = api.baseUrl.toString()
        _api.value = api
        watch(api)
        return api
    }

    fun onSignedIn(user: Me) { _me.value = user }

    fun refreshMe() {
        val api = _api.value ?: return
        if (!api.isSignedIn) { _me.value = null; return }
        scope.launch {
            try {
                _me.value = api.me()
            } catch (e: ApiException.Http) {
                if (e.status == 401 || e.status == 403) _me.value = null
            } catch (_: ApiException) {
                // Offline: keep the session; the profile refreshes on the next successful call.
            }
        }
    }

    suspend fun signOut() {
        _api.value?.logout()
        _me.value = null
    }

    fun notify(message: String) { _messages.tryEmit(message) }

    private fun watch(api: ThreadhallApi) {
        sessionWatcher?.cancel()
        sessionWatcher = scope.launch {
            api.sessionEvents.collect { event ->
                if (event is SessionEvent.SignedOut) {
                    _me.value = null
                    _messages.tryEmit("Your session ended. Please sign in again.")
                }
            }
        }
    }

    private fun build(url: String) = ThreadhallApi(url, tokenStore, userAgent)
}
