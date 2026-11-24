package dev.threadhall.app.ui.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.threadhall.app.BuildConfig
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.relativeAge
import kotlinx.coroutines.launch

@Composable
fun ProfileScreen(container: AppContainer, onSignIn: () -> Unit, onChangeServer: () -> Unit, onMyPosts: (String) -> Unit) {
    val me by container.me.collectAsStateWithLifecycle()
    val api by container.api.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        val user = me
        if (user == null) {
            Text("You're browsing anonymously", style = MaterialTheme.typography.titleLarge)
            Text("Sign in to post, comment, vote and join communities.", style = MaterialTheme.typography.bodyMedium)
            Button(onClick = onSignIn, modifier = Modifier.fillMaxWidth().testTag("profile_sign_in")) { Text("Sign in or create account") }
        } else {
            Text("u/${user.handle}", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, modifier = Modifier.testTag("profile_handle"))
            user.displayName?.let { Text(it, style = MaterialTheme.typography.titleMedium) }
            Text("${user.postKarma} post karma · ${user.commentKarma} comment karma", modifier = Modifier.testTag("profile_karma"))
            Text("Joined ${relativeAge(user.createdAt)} ago", style = MaterialTheme.typography.labelSmall)
            user.bio?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
            OutlinedButton(onClick = { onMyPosts(user.handle) }, modifier = Modifier.fillMaxWidth()) { Text("My posts") }
            OutlinedButton(onClick = { container.refreshMe() }, modifier = Modifier.fillMaxWidth()) { Text("Refresh") }
            Button(onClick = { scope.launch { container.signOut() } }, modifier = Modifier.fillMaxWidth().testTag("sign_out")) { Text("Sign out") }
        }
        HorizontalDivider()
        Text("Server", style = MaterialTheme.typography.titleMedium)
        Text(api?.baseUrl?.toString() ?: "Not configured", style = MaterialTheme.typography.bodyMedium)
        if (api?.isCleartext == true) {
            Text("Unencrypted connection (http). Use only on a trusted private network.", color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.labelSmall)
        }
        OutlinedButton(onClick = onChangeServer, modifier = Modifier.fillMaxWidth()) { Text("Change server") }
        HorizontalDivider()
        Text(
            "Threadhall ${BuildConfig.VERSION_NAME} (working name). Independent, self-hosted community app; not affiliated with Reddit. " +
                "Your account exists only on the server above.",
            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
