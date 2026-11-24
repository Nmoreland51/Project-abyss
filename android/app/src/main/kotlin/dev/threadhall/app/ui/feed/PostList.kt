package dev.threadhall.app.ui.feed

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dev.threadhall.app.ui.common.CenteredMessage
import dev.threadhall.app.ui.common.LoadingRow
import dev.threadhall.app.ui.common.VoteColumn
import dev.threadhall.app.ui.common.needsSignIn
import dev.threadhall.app.ui.common.relativeAge
import dev.threadhall.app.ui.common.userMessage
import dev.threadhall.core.Post
import dev.threadhall.core.PostPage
import dev.threadhall.core.ThreadhallApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class PostListState(
    val items: List<Post> = emptyList(),
    val nextCursor: String? = null,
    val loading: Boolean = false,
    val refreshing: Boolean = false,
    val loadedOnce: Boolean = false,
    val error: String? = null,
    val pendingVotes: Set<String> = emptySet(),
)

/** Cursor-paged list of posts. The server is authoritative: votes update only after confirmation. */
class PostListViewModel(
    private val api: () -> ThreadhallApi,
    private val loader: suspend (ThreadhallApi, String?) -> PostPage,
    private val onNeedSignIn: () -> Unit,
    private val onMessage: (String) -> Unit,
    contentChanges: Flow<Long> = emptyFlow(),
) : ViewModel() {
    private val _state = MutableStateFlow(PostListState())
    val state: StateFlow<PostListState> = _state.asStateFlow()
    private var job: Job? = null

    init {
        refresh()
        viewModelScope.launch { contentChanges.drop(1).collect { refresh() } }
    }

    fun refresh() {
        job?.cancel()
        _state.update { it.copy(refreshing = it.loadedOnce, loading = !it.loadedOnce, error = null) }
        job = viewModelScope.launch {
            try {
                val page = loader(api(), null)
                _state.update { it.copy(items = page.items, nextCursor = page.nextCursor, loading = false, refreshing = false, loadedOnce = true) }
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                _state.update { it.copy(loading = false, refreshing = false, loadedOnce = true, error = e.userMessage()) }
            }
        }
    }

    fun loadMore() {
        val s = _state.value
        if (s.loading || s.refreshing || s.nextCursor == null) return
        _state.update { it.copy(loading = true) }
        job = viewModelScope.launch {
            try {
                val page = loader(api(), s.nextCursor)
                _state.update { cur ->
                    val seen = cur.items.mapTo(HashSet()) { it.id }
                    cur.copy(items = cur.items + page.items.filter { it.id !in seen }, nextCursor = page.nextCursor, loading = false)
                }
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                _state.update { it.copy(loading = false) }
                onMessage(e.userMessage())
            }
        }
    }

    fun vote(post: Post, value: Int) {
        if (post.id in _state.value.pendingVotes) return
        _state.update { it.copy(pendingVotes = it.pendingVotes + post.id) }
        viewModelScope.launch {
            try {
                val result = api().votePost(post.id, value)
                _state.update { s ->
                    s.copy(items = s.items.map { if (it.id == post.id) it.copy(score = result.score, myVote = result.myVote) else it })
                }
            } catch (e: Exception) {
                if (e.needsSignIn()) onNeedSignIn() else onMessage(e.userMessage())
            } finally {
                _state.update { it.copy(pendingVotes = it.pendingVotes - post.id) }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PostList(
    state: PostListState,
    signedIn: Boolean,
    onRefresh: () -> Unit,
    onLoadMore: () -> Unit,
    onVote: (Post, Int) -> Unit,
    onOpen: (Post) -> Unit,
    onOpenCommunity: ((String) -> Unit)?,
    emptyText: String,
    emptyAction: Pair<String, () -> Unit>? = null,
    header: (LazyListScope.() -> Unit)? = null,
) {
    val listState = rememberLazyListState()
    val nearEnd by remember {
        derivedStateOf {
            val last = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
            last >= listState.layoutInfo.totalItemsCount - 5
        }
    }
    LaunchedEffect(nearEnd, state.items.size) { if (nearEnd && state.items.isNotEmpty()) onLoadMore() }
    PullToRefreshBox(isRefreshing = state.refreshing, onRefresh = onRefresh, modifier = Modifier.fillMaxSize()) {
        LazyColumn(Modifier.fillMaxSize().testTag("post_list"), state = listState, contentPadding = PaddingValues(bottom = 88.dp)) {
            header?.invoke(this)
            if (state.error != null && state.items.isEmpty()) {
                item { CenteredMessage(state.error, "Retry", onRefresh) }
            } else if (state.loadedOnce && state.items.isEmpty() && !state.loading) {
                item { CenteredMessage(emptyText, emptyAction?.first, emptyAction?.second) }
            }
            items(state.items, key = { it.id }) { post ->
                PostRow(
                    post = post,
                    pending = post.id in state.pendingVotes,
                    canVote = post.isVisible,
                    onVote = { v -> onVote(post, v) },
                    onOpen = { onOpen(post) },
                    onOpenCommunity = onOpenCommunity,
                    signedIn = signedIn,
                )
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            }
            if (state.loading) item { LoadingRow() }
        }
    }
}

@Composable
fun PostRow(
    post: Post,
    pending: Boolean,
    canVote: Boolean,
    onVote: (Int) -> Unit,
    onOpen: () -> Unit,
    onOpenCommunity: ((String) -> Unit)?,
    signedIn: Boolean,
) {
    Surface(color = MaterialTheme.colorScheme.surface) {
        Row(
            Modifier.fillMaxWidth().clickable(role = Role.Button, onClickLabel = "Open discussion", onClick = onOpen)
                .padding(end = 12.dp, top = 4.dp, bottom = 4.dp).testTag("post_row_${post.id}"),
            verticalAlignment = Alignment.Top,
        ) {
            VoteColumn(post.score, post.myVote, pending, enabled = canVote, onVote = onVote)
            Column(Modifier.weight(1f).padding(top = 6.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                if (post.flair != null) {
                    Text(post.flair!!, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary,
                        fontWeight = FontWeight.SemiBold)
                }
                Text(post.title, style = MaterialTheme.typography.titleMedium, maxLines = 3, overflow = TextOverflow.Ellipsis)
                if (post.kind == "link" && post.urlDomain != null) {
                    Text("(${post.urlDomain})", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary)
                }
                val meta = buildString {
                    append("c/${post.community.slug}")
                    append(" · ")
                    append(post.author?.let { "u/${it.handle}" } ?: "[deleted]")
                    append(" · ")
                    append(relativeAge(post.createdAt))
                    if (post.origin == "historical") append(" · archived")
                }
                Text(
                    meta, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1, overflow = TextOverflow.Ellipsis,
                    modifier = if (onOpenCommunity != null) Modifier.clickable { onOpenCommunity(post.community.slug) } else Modifier,
                )
                Text(
                    "${post.commentCount} comment${if (post.commentCount == 1) "" else "s"}",
                    style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
