package dev.threadhall.app.ui.post

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.CenteredMessage
import dev.threadhall.app.ui.common.LoadingRow
import dev.threadhall.app.ui.common.VoteColumn
import dev.threadhall.app.ui.common.relativeAge
import dev.threadhall.core.CommentNode
import dev.threadhall.core.CommentSort
import dev.threadhall.core.Me
import dev.threadhall.core.Post
import kotlinx.coroutines.launch
import java.util.UUID

private const val MAX_VISUAL_INDENT = 6
private val threadColors = listOf(0xFF7FB8E6, 0xFF5FB58A, 0xFFE0B15A, 0xFFB98AD9, 0xFFE38A8A, 0xFF7FCFCF)

private data class ReplyTarget(val parentId: String?, val quote: String)

@Composable
fun PostScreen(
    container: AppContainer,
    postId: String,
    onNeedSignIn: () -> Unit,
    onOpenCommunity: (String) -> Unit,
    onDeleted: () -> Unit,
) {
    val me by container.me.collectAsStateWithLifecycle()
    val vm: PostViewModel = viewModel(key = "post:$postId:${me?.id}") { PostViewModel(container, postId, onNeedSignIn) }
    val state by vm.state.collectAsStateWithLifecycle()
    var replyTarget by remember { mutableStateOf<ReplyTarget?>(null) }
    var confirmDeletePost by remember { mutableStateOf(false) }

    LaunchedEffect(state.deleted) { if (state.deleted) onDeleted() }

    fun startReply(parentId: String?, quote: String) {
        if (me == null) onNeedSignIn() else replyTarget = ReplyTarget(parentId, quote)
    }

    val post = state.post
    Column(Modifier.fillMaxSize()) {
    LazyColumn(Modifier.weight(1f).fillMaxWidth().testTag("thread")) {
        when {
            post == null && state.loading -> item { LoadingRow() }
            post == null -> item { CenteredMessage(state.error ?: "Post not available", "Retry", vm::load) }
            else -> {
                item(key = "post") {
                    PostHeader(post, me, pending = "post" in state.pending, onVote = vm::votePost,
                        onOpenCommunity = onOpenCommunity, onReply = { startReply(null, post.title) },
                        onDelete = { confirmDeletePost = true })
                }
                item(key = "sort") {
                    Row(Modifier.padding(horizontal = 12.dp, vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        CommentSort.entries.forEach { s -> FilterChip(selected = s == state.sort, onClick = { vm.setSort(s) }, label = { Text(s.label) }) }
                    }
                }
                if (state.loading) item { LoadingRow() }
                if (!state.loading && state.roots.isEmpty()) item { CenteredMessage("No comments yet. Start the discussion.") }
                items(flatten(state.roots, state.collapsed), key = { it.key }) { line ->
                    when (line) {
                        is ThreadLine.Comment -> CommentRow(
                            node = line.node, collapsed = line.collapsed, me = me, pending = line.node.id in state.pending,
                            onToggle = { vm.toggleCollapse(line.node.id) },
                            onVote = { v -> if (me == null) onNeedSignIn() else vm.voteComment(line.node.id, v) },
                            onReply = { startReply(line.node.id, line.node.body.orEmpty()) },
                            onDelete = { vm.deleteComment(line.node.id) },
                        )
                        is ThreadLine.More -> MoreRepliesRow(line, loading = "more-${line.parentId}" in state.pending) { vm.loadReplies(line.parentId) }
                    }
                }
                if (state.nextCursor != null) {
                    item(key = "more-roots") {
                        TextButton(onClick = vm::loadMoreRoots, enabled = !state.loadingMoreRoots, modifier = Modifier.padding(12.dp)) {
                            Text(if (state.loadingMoreRoots) "Loading…" else "Load more comments")
                        }
                    }
                }
            }
        }
    }

    replyTarget?.let { target ->
        ReplyComposer(target, onDismiss = { replyTarget = null }) { body, key -> vm.reply(target.parentId, body, key) }
    }
    }
    if (confirmDeletePost) {
        AlertDialog(
            onDismissRequest = { confirmDeletePost = false },
            title = { Text("Delete post?") },
            text = { Text("The post will show as [deleted]. Comments stay visible.") },
            confirmButton = { TextButton(onClick = { confirmDeletePost = false; vm.deletePost() }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmDeletePost = false }) { Text("Cancel") } },
        )
    }
}

@Composable
private fun PostHeader(
    post: Post,
    me: Me?,
    pending: Boolean,
    onVote: (Int) -> Unit,
    onOpenCommunity: (String) -> Unit,
    onReply: () -> Unit,
    onDelete: () -> Unit,
) {
    val uri = LocalUriHandler.current
    Column(Modifier.fillMaxWidth().padding(end = 12.dp, top = 8.dp)) {
        Row(verticalAlignment = Alignment.Top) {
            VoteColumn(post.score, post.myVote, pending, enabled = post.isVisible && me != null, onVote = onVote)
            Column(Modifier.weight(1f).padding(top = 6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    "c/${post.community.slug} · ${post.author?.let { "u/${it.handle}" } ?: "[deleted]"} · ${relativeAge(post.createdAt)}" +
                        (if (post.editedAt != null) " · edited" else ""),
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.clickable { onOpenCommunity(post.community.slug) },
                )
                post.flair?.let { Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary) }
                SelectionContainer { Text(post.title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold) }
                if (post.kind == "link" && post.url != null) {
                    OutlinedButton(onClick = { uri.openUri(post.url!!) }, modifier = Modifier.semantics { contentDescription = "Open link ${post.urlDomain}" }) {
                        Text("Open ${post.urlDomain ?: "link"} ↗", maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
                post.body?.takeIf { it.isNotBlank() }?.let { SelectionContainer { Text(it, style = MaterialTheme.typography.bodyMedium) } }
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("${post.commentCount} comments", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold)
                    if (post.isVisible) TextButton(onClick = onReply, modifier = Modifier.testTag("reply_post")) { Text("Comment") }
                    if (post.isVisible && me != null && post.author?.id == me.id) TextButton(onClick = onDelete) { Text("Delete") }
                }
            }
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
    }
}

@Composable
private fun CommentRow(
    node: CommentNode,
    collapsed: Boolean,
    me: Me?,
    pending: Boolean,
    onToggle: () -> Unit,
    onVote: (Int) -> Unit,
    onReply: () -> Unit,
    onDelete: () -> Unit,
) {
    val indent = node.depth.coerceAtMost(MAX_VISUAL_INDENT)
    Row(
        Modifier.fillMaxWidth().height(IntrinsicSize.Min).padding(start = (8 + indent * 12).dp, end = 8.dp)
            .testTag("comment_${node.id}")
            .semantics { stateDescription = if (collapsed) "Collapsed" else "Expanded" },
    ) {
        if (node.depth > 0) {
            Box(Modifier.width(2.dp).fillMaxHeight().background(androidx.compose.ui.graphics.Color(threadColors[(node.depth - 1) % threadColors.size])))
        }
        Column(Modifier.weight(1f).padding(start = 8.dp, top = 6.dp, bottom = 2.dp)) {
            Row(Modifier.fillMaxWidth().clickable(onClickLabel = if (collapsed) "Expand" else "Collapse", onClick = onToggle),
                verticalAlignment = Alignment.CenterVertically) {
                Text(
                    buildString {
                        append(node.author?.let { "u/${it.handle}" } ?: "[deleted]")
                        append(" · ${node.score} pt${if (node.score == 1 || node.score == -1) "" else "s"} · ${relativeAge(node.createdAt)}")
                        if (node.editedAt != null && node.isVisible) append(" · edited")
                        if (node.depth > MAX_VISUAL_INDENT) append(" · level ${node.depth}")
                        if (collapsed) append("  [+${node.replyCount}]")
                    },
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (!collapsed) {
                SelectionContainer {
                    Text(node.body.orEmpty(), style = MaterialTheme.typography.bodyMedium,
                        color = if (node.isVisible) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (node.isVisible) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        val votes = dev.threadhall.app.ui.theme.LocalVoteColors.current
                        TextButton(onClick = { onVote(if (node.myVote == 1) 0 else 1) }, enabled = !pending) {
                            Text("▲", color = if (node.myVote == 1) votes.up else votes.neutral,
                                modifier = Modifier.semantics { contentDescription = if (node.myVote == 1) "Remove upvote" else "Upvote comment" })
                        }
                        TextButton(onClick = { onVote(if (node.myVote == -1) 0 else -1) }, enabled = !pending) {
                            Text("▼", color = if (node.myVote == -1) votes.down else votes.neutral,
                                modifier = Modifier.semantics { contentDescription = if (node.myVote == -1) "Remove downvote" else "Downvote comment" })
                        }
                        TextButton(onClick = onReply, modifier = Modifier.testTag("reply_${node.id}")) { Text("Reply") }
                        if (me != null && node.author?.id == me.id) TextButton(onClick = onDelete, enabled = !pending) { Text("Delete") }
                    }
                }
            }
        }
    }
}

@Composable
private fun MoreRepliesRow(line: ThreadLine.More, loading: Boolean, onClick: () -> Unit) {
    val indent = line.depth.coerceAtMost(MAX_VISUAL_INDENT)
    TextButton(onClick = onClick, enabled = !loading, modifier = Modifier.padding(start = (8 + indent * 12).dp)) {
        Text(if (loading) "Loading…" else "Continue thread (${line.count} more ${if (line.count == 1) "reply" else "replies"})")
    }
}

/** Inline composer docked above the keyboard (no modal window). */
@Composable
private fun ReplyComposer(target: ReplyTarget, onDismiss: () -> Unit, submit: suspend (String, String) -> String?) {
    var body by rememberSaveable(target) { mutableStateOf("") }
    // One key per draft: a retried submit after a timeout cannot create a duplicate comment.
    var key by rememberSaveable(target) { mutableStateOf(UUID.randomUUID().toString()) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread
    Surface(tonalElevation = 3.dp, shadowElevation = 6.dp, modifier = Modifier.fillMaxWidth().imePadding()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                (if (target.parentId == null) "Commenting on: " else "Replying to: ") + target.quote,
                maxLines = 2, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.labelSmall,
            )
            OutlinedTextField(body, { body = it.take(10000); key = UUID.randomUUID().toString(); error = null },
                minLines = 3, maxLines = 8, modifier = Modifier.fillMaxWidth().testTag("reply_body"), label = { Text("Your reply") })
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancel") }
                Button(enabled = !busy && body.isNotBlank(), modifier = Modifier.testTag("reply_submit"), onClick = {
                    busy = true
                    scope.launch {
                        error = submit(body, key)
                        busy = false
                        if (error == null) onDismiss()
                    }
                }) { Text(if (busy) "Sending…" else "Send") }
            }
        }
    }
}
