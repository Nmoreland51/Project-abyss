package dev.threadhall.app.ui.setup

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import dev.threadhall.app.BuildConfig
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.userMessage
import dev.threadhall.core.ThreadhallApi
import dev.threadhall.core.TokenStore
import dev.threadhall.core.Tokens
import kotlinx.coroutines.launch

private object NoTokens : TokenStore {
    override fun load(): Tokens? = null
    override fun save(tokens: Tokens) = Unit
    override fun clear() = Unit
}

/**
 * First-run (and Settings) screen: the user points the app at THEIR server. The app has no
 * built-in or third-party server; it never contacts any host other than this one.
 */
@Composable
fun ServerSetupScreen(container: AppContainer, initial: String?, onConnected: () -> Unit) {
    var url by rememberSaveable { mutableStateOf(initial ?: "") }
    var busy by rememberSaveable { mutableStateOf(false) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("Connect to a server", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Threadhall is a self-hosted community app. Enter the address of the server you run or were invited to, " +
                "for example http://192.168.1.20:8000 on your home network or https://forum.example.org.",
            style = MaterialTheme.typography.bodyMedium,
        )
        OutlinedTextField(
            value = url,
            onValueChange = { url = it; error = null },
            label = { Text("Server address") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri, imeAction = ImeAction.Go),
            modifier = Modifier.fillMaxWidth().testTag("server_url"),
        )
        if (url.trim().startsWith("http://") || (url.isNotBlank() && "://" !in url)) {
            Text(
                if (BuildConfig.DEBUG) "http:// is unencrypted. Use it only on a network you trust (pilot build)."
                else "This build requires https://.",
                color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall,
            )
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(
            enabled = !busy && url.isNotBlank(),
            modifier = Modifier.fillMaxWidth().testTag("connect"),
            onClick = {
                busy = true
                scope.launch {
                    try {
                        val probe = ThreadhallApi(url, NoTokens)
                        val health = if (probe.isCleartext && !BuildConfig.DEBUG) null else probe.health()
                        if (health == null) {
                            error = "This build only connects to https:// servers."
                        } else if (health.status != "ok") {
                            error = "Server is up but not ready: ${health.checks}"
                        } else {
                            container.setServer(url)
                            container.refreshMe()
                            onConnected()
                        }
                    } catch (e: Exception) {
                        if (e is kotlinx.coroutines.CancellationException) throw e
                        error = e.userMessage()
                    } finally {
                        busy = false
                    }
                }
            },
        ) {
            if (busy) CircularProgressIndicator(Modifier.padding(2.dp), strokeWidth = 2.dp) else Text("Connect")
        }
        Text(
            "Not affiliated with Reddit. Accounts are local to the server you connect to.",
            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
