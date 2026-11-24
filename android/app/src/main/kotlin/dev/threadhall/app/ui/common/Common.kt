package dev.threadhall.app.ui.common

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.threadhall.app.ui.theme.LocalVoteColors
import dev.threadhall.core.ApiException
import java.time.Duration
import java.time.Instant
import java.time.OffsetDateTime

/** Human-readable message for any failure; never shows stack traces or tokens. Unexpected
 * (non-API) failures are logged with their type so they are diagnosable. */
fun Throwable.userMessage(): String {
    if (this !is ApiException) android.util.Log.w("Threadhall", "Unexpected failure", this)
    return describe()
}

private fun Throwable.describe(): String = when (this) {
    is ApiException.Network -> "Can't reach the server. Check your connection and the server address."
    is ApiException.Http -> when (status) {
        401 -> "Please sign in to do that."
        429 -> "Too many requests. Wait a minute and try again."
        in 500..599 -> "The server had a problem (${requestId ?: "no request id"}). Try again."
        else -> details.firstOrNull()?.message ?: message
    }
    is ApiException.Protocol -> "Unexpected response from the server. The app may need an update."
    is IllegalArgumentException -> message ?: "Invalid input"
    else -> "Something went wrong."
}

fun Throwable.needsSignIn(): Boolean = this is ApiException.Http && status == 401

/** Compact relative age: "now", "5m", "3h", "2d", "4mo", "1y". */
fun relativeAge(iso: String, now: Instant = Instant.now()): String {
    val then = runCatching { OffsetDateTime.parse(iso).toInstant() }.getOrNull() ?: return ""
    val d = Duration.between(then, now)
    return when {
        d.toMinutes() < 1 -> "now"
        d.toHours() < 1 -> "${d.toMinutes()}m"
        d.toDays() < 1 -> "${d.toHours()}h"
        d.toDays() < 30 -> "${d.toDays()}d"
        d.toDays() < 365 -> "${d.toDays() / 30}mo"
        else -> "${d.toDays() / 365}y"
    }
}

fun compactCount(n: Int): String = when {
    n >= 1_000_000 || n <= -1_000_000 -> "%.1fm".format(n / 1_000_000.0)
    n >= 10_000 || n <= -10_000 -> "${n / 1000}k"
    n >= 1_000 || n <= -1_000 -> "%.1fk".format(n / 1000.0)
    else -> n.toString()
}

/** Classic vertical vote control. Arrows are disabled while a vote is awaiting server confirmation. */
@Composable
fun VoteColumn(score: Int, myVote: Int, pending: Boolean, enabled: Boolean, onVote: (Int) -> Unit, modifier: Modifier = Modifier) {
    val colors = LocalVoteColors.current
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        IconButton(onClick = { onVote(if (myVote == 1) 0 else 1) }, enabled = enabled && !pending, modifier = Modifier.size(40.dp)) {
            Icon(Icons.Filled.KeyboardArrowUp, contentDescription = if (myVote == 1) "Remove upvote" else "Upvote",
                tint = if (myVote == 1) colors.up else colors.neutral)
        }
        Box(Modifier.semantics { contentDescription = "Score $score" }, contentAlignment = Alignment.Center) {
            if (pending) CircularProgressIndicator(Modifier.size(14.dp), strokeWidth = 2.dp)
            else Text(
                compactCount(score), style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold,
                color = when (myVote) { 1 -> colors.up; -1 -> colors.down; else -> MaterialTheme.colorScheme.onSurface },
            )
        }
        IconButton(onClick = { onVote(if (myVote == -1) 0 else -1) }, enabled = enabled && !pending, modifier = Modifier.size(40.dp)) {
            Icon(Icons.Filled.KeyboardArrowDown, contentDescription = if (myVote == -1) "Remove downvote" else "Downvote",
                tint = if (myVote == -1) colors.down else colors.neutral)
        }
    }
}

@Composable
fun CenteredMessage(text: String, actionLabel: String? = null, onAction: (() -> Unit)? = null) {
    Column(
        Modifier.fillMaxWidth().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(text, textAlign = TextAlign.Center, style = MaterialTheme.typography.bodyMedium)
        if (actionLabel != null && onAction != null) OutlinedButton(onClick = onAction) { Text(actionLabel) }
    }
}

@Composable
fun LoadingRow() {
    Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
}
