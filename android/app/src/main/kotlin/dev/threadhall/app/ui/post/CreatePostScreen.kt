package dev.threadhall.app.ui.post

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.userMessage
import dev.threadhall.core.ApiException
import kotlinx.coroutines.launch
import java.util.UUID

/**
 * New text or link post. The idempotency key is created once per draft and survives process
 * death, so pressing Submit again after a timeout can never create a duplicate post.
 */
@Composable
fun CreatePostScreen(container: AppContainer, initialCommunity: String?, onPosted: (String) -> Unit) {
    var community by rememberSaveable { mutableStateOf(initialCommunity ?: "") }
    var isLink by rememberSaveable { mutableStateOf(false) }
    var title by rememberSaveable { mutableStateOf("") }
    var body by rememberSaveable { mutableStateOf("") }
    var url by rememberSaveable { mutableStateOf("") }
    var draftKey by rememberSaveable { mutableStateOf(UUID.randomUUID().toString()) }
    var busy by rememberSaveable { mutableStateOf(false) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    var choices by remember { mutableStateOf(emptyList<String>()) }
    var menu by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread

    LaunchedEffect(Unit) {
        choices = runCatching { container.requireApi().myCommunities().map { it.slug } }.getOrDefault(emptyList())
        if (community.isBlank() && choices.size == 1) community = choices.first()
    }

    // Any edit to the content is a new logical request and needs a new key.
    fun edited() { draftKey = UUID.randomUUID().toString(); error = null }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Box {
            OutlinedButton(onClick = { menu = true }, modifier = Modifier.fillMaxWidth().testTag("choose_community")) {
                Text(if (community.isBlank()) "Choose a community" else "c/$community")
            }
            DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                if (choices.isEmpty()) DropdownMenuItem(text = { Text("Join a community first") }, onClick = { menu = false })
                choices.forEach { slug ->
                    DropdownMenuItem(text = { Text("c/$slug") }, onClick = { community = slug; menu = false; edited() })
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = !isLink, onClick = { isLink = false; edited() }, label = { Text("Text") })
            FilterChip(selected = isLink, onClick = { isLink = true; edited() }, label = { Text("Link") })
        }
        OutlinedTextField(title, { title = it.take(300); edited() }, label = { Text("Title") },
            modifier = Modifier.fillMaxWidth().testTag("post_title"), supportingText = { Text("${title.length}/300") })
        if (isLink) {
            OutlinedTextField(url, { url = it.trim(); edited() }, label = { Text("https://…") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                modifier = Modifier.fillMaxWidth().testTag("post_url"))
        } else {
            OutlinedTextField(body, { body = it; edited() }, label = { Text("Text (optional)") }, minLines = 5,
                modifier = Modifier.fillMaxWidth().testTag("post_body"))
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(
            enabled = !busy && community.isNotBlank() && title.isNotBlank() && (!isLink || url.isNotBlank()),
            modifier = Modifier.fillMaxWidth().testTag("post_submit"),
            onClick = {
                busy = true
                scope.launch {
                    try {
                        val api = container.requireApi()
                        val post = if (isLink) api.createLinkPost(community, title, url, draftKey)
                        else api.createTextPost(community, title, body, draftKey)
                        container.markContentChanged()
                        onPosted(post.id)
                    } catch (e: Exception) {
                        if (e is kotlinx.coroutines.CancellationException) throw e
                        error = e.userMessage() +
                            if (e is ApiException.Network) " Submitting again is safe: it will not create a duplicate." else ""
                    } finally {
                        busy = false
                    }
                }
            },
        ) { Text(if (busy) "Posting…" else "Post") }
    }
}
