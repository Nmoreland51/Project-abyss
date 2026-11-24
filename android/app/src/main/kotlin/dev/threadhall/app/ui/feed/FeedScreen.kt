package dev.threadhall.app.ui.feed

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import dev.threadhall.app.data.AppContainer
import dev.threadhall.core.FeedScope
import dev.threadhall.core.Post
import dev.threadhall.core.PostSort
import dev.threadhall.core.TimeWindow

@Composable
fun SortBar(sort: PostSort, window: TimeWindow, onSort: (PostSort) -> Unit, onWindow: (TimeWindow) -> Unit) {
    var menu by remember { mutableStateOf(false) }
    Surface(color = MaterialTheme.colorScheme.surface, tonalElevation = 1.dp) {
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            PostSort.entries.forEach { s ->
                FilterChip(selected = s == sort, onClick = { onSort(s) }, label = { Text(s.label) })
            }
            if (sort == PostSort.TOP || sort == PostSort.CONTROVERSIAL) {
                Box {
                    TextButton(onClick = { menu = true }) { Text(window.label) }
                    DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                        TimeWindow.entries.forEach { w ->
                            DropdownMenuItem(text = { Text(w.label) }, onClick = { menu = false; onWindow(w) })
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CleartextBanner(visible: Boolean) {
    if (!visible) return
    Surface(color = MaterialTheme.colorScheme.errorContainer) {
        Text(
            "Unencrypted http:// connection — pilot use on a trusted network only",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onErrorContainer,
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),
        )
    }
}

@Composable
fun FeedScreen(
    container: AppContainer,
    scope: FeedScope,
    onOpenPost: (Post) -> Unit,
    onOpenCommunity: (String) -> Unit,
    onNeedSignIn: () -> Unit,
    onBrowseCommunities: () -> Unit,
) {
    var sort by rememberSaveable(scope) { mutableStateOf(PostSort.HOT) }
    var window by rememberSaveable(scope) { mutableStateOf(TimeWindow.DAY) }
    val me by container.me.collectAsStateWithLifecycle()
    val api by container.api.collectAsStateWithLifecycle()
    val vm: PostListViewModel = viewModel(key = "feed:${scope.wire}:${sort.wire}:${window.wire}:${me?.id}") {
        PostListViewModel(
            api = container::requireApi,
            loader = { a, cursor -> a.feed(scope, sort, window, cursor) },
            onNeedSignIn = onNeedSignIn,
            onMessage = container::notify,
            contentChanges = container.contentVersion,
        )
    }
    val state by vm.state.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize()) {
        CleartextBanner(api?.isCleartext == true)
        SortBar(sort, window, { sort = it }, { window = it })
        val signedOutHome = scope == FeedScope.HOME && me == null
        PostList(
            state = state,
            signedIn = me != null,
            onRefresh = vm::refresh,
            onLoadMore = vm::loadMore,
            onVote = vm::vote,
            onOpen = onOpenPost,
            onOpenCommunity = onOpenCommunity,
            emptyText = when {
                scope == FeedScope.HOME && me != null -> "Your Home feed shows posts from communities you join. Join a few to get started."
                signedOutHome -> "Nothing here yet."
                else -> "No posts yet. Start a community and write the first post."
            },
            emptyAction = "Browse communities" to onBrowseCommunities,
        )
    }
}
