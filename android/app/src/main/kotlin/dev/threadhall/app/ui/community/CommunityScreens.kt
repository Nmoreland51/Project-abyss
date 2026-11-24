package dev.threadhall.app.ui.community

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.CenteredMessage
import dev.threadhall.app.ui.common.LoadingRow
import dev.threadhall.app.ui.common.needsSignIn
import dev.threadhall.app.ui.common.userMessage
import dev.threadhall.app.ui.feed.PostList
import dev.threadhall.app.ui.feed.PostListViewModel
import dev.threadhall.app.ui.feed.SortBar
import dev.threadhall.core.Community
import dev.threadhall.core.Post
import dev.threadhall.core.PostSort
import dev.threadhall.core.TimeWindow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

// ---------------- browse ----------------

data class BrowseState(
    val query: String = "",
    val items: List<Community> = emptyList(),
    val mine: List<Community> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
)

class BrowseViewModel(private val container: AppContainer) : ViewModel() {
    private val _state = MutableStateFlow(BrowseState())
    val state = _state.asStateFlow()

    init {
        load()
        viewModelScope.launch { container.contentVersion.drop(1).collect { load() } }
    }

    fun setQuery(q: String) { _state.update { it.copy(query = q) }; load() }

    fun load() {
        val q = _state.value.query
        _state.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            try {
                val api = container.requireApi()
                val all = api.communities(prefix = q.trim().lowercase().ifBlank { null })
                val mine = if (api.isSignedIn && q.isBlank()) runCatching { api.myCommunities() }.getOrDefault(emptyList()) else emptyList()
                _state.update { it.copy(items = all.items, mine = mine, loading = false) }
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                _state.update { it.copy(loading = false, error = e.userMessage()) }
            }
        }
    }
}

@Composable
fun CommunitiesScreen(container: AppContainer, onOpen: (String) -> Unit, onCreate: () -> Unit) {
    val me by container.me.collectAsStateWithLifecycle()
    val vm: BrowseViewModel = viewModel(key = "browse:${me?.id}") { BrowseViewModel(container) }
    val state by vm.state.collectAsStateWithLifecycle()
    LazyColumn(Modifier.fillMaxSize().testTag("community_list")) {
        item {
            Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = state.query, onValueChange = vm::setQuery, singleLine = true,
                    label = { Text("Find a community") }, modifier = Modifier.weight(1f),
                )
                Button(onClick = onCreate, modifier = Modifier.testTag("create_community")) { Text("Create") }
            }
        }
        if (state.mine.isNotEmpty()) {
            item { SectionLabel("Your communities") }
            items(state.mine, key = { "mine-" + it.id }) { CommunityRow(it, onOpen) }
            item { SectionLabel("All communities") }
        }
        if (state.loading) item { LoadingRow() }
        state.error?.let { err -> item { CenteredMessage(err, "Retry", vm::load) } }
        if (!state.loading && state.error == null && state.items.isEmpty()) {
            item { CenteredMessage("No communities yet. Create the first one.") }
        }
        items(state.items, key = { it.id }) { CommunityRow(it, onOpen) }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(text, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.secondary,
        modifier = Modifier.padding(start = 16.dp, top = 12.dp, bottom = 4.dp))
}

@Composable
private fun CommunityRow(c: Community, onOpen: (String) -> Unit) {
    Column(Modifier.fillMaxWidth().clickable { onOpen(c.slug) }.padding(horizontal = 16.dp, vertical = 10.dp)) {
        Text("c/${c.slug}", style = MaterialTheme.typography.titleMedium)
        Text(
            "${c.subscriberCount} member${if (c.subscriberCount == 1) "" else "s"}" + (if (c.membership?.subscribed == true) " · joined" else ""),
            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (c.description.isNotBlank()) Text(c.description, style = MaterialTheme.typography.bodyMedium, maxLines = 2)
    }
    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
}

// ---------------- single community ----------------

class CommunityHeaderViewModel(private val container: AppContainer, private val slug: String) : ViewModel() {
    val community = MutableStateFlow<Community?>(null)
    val error = MutableStateFlow<String?>(null)
    val busy = MutableStateFlow(false)

    init { load() }

    fun load() = viewModelScope.launch {
        try {
            community.value = container.requireApi().community(slug); error.value = null
        } catch (e: Exception) {
            if (e is kotlinx.coroutines.CancellationException) throw e
            error.value = e.userMessage()
        }
    }

    fun toggleMembership(onNeedSignIn: () -> Unit) {
        val c = community.value ?: return
        busy.value = true
        viewModelScope.launch {
            try {
                val api = container.requireApi()
                community.value = if (c.membership?.subscribed == true) api.unsubscribe(slug) else api.subscribe(slug)
                container.markContentChanged() // Home feed membership changed
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                if (e.needsSignIn()) onNeedSignIn() else container.notify(e.userMessage())
            } finally {
                busy.value = false
            }
        }
    }
}

@Composable
fun CommunityScreen(
    container: AppContainer,
    slug: String,
    onOpenPost: (Post) -> Unit,
    onNeedSignIn: () -> Unit,
) {
    val me by container.me.collectAsStateWithLifecycle()
    var sort by rememberSaveable { mutableStateOf(PostSort.HOT) }
    var window by rememberSaveable { mutableStateOf(TimeWindow.DAY) }
    val header: CommunityHeaderViewModel = viewModel(key = "community-header:$slug:${me?.id}") { CommunityHeaderViewModel(container, slug) }
    val list: PostListViewModel = viewModel(key = "community:$slug:${sort.wire}:${window.wire}:${me?.id}") {
        PostListViewModel(container::requireApi, { a, cursor -> a.communityPosts(slug, sort, window, cursor) }, onNeedSignIn,
            container::notify, container.contentVersion)
    }
    val community by header.community.collectAsStateWithLifecycle()
    val headerError by header.error.collectAsStateWithLifecycle()
    val busy by header.busy.collectAsStateWithLifecycle()
    val state by list.state.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(community?.displayName ?: "c/$slug", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("c/$slug · ${community?.subscriberCount ?: 0} members", style = MaterialTheme.typography.labelSmall)
                }
                val joined = community?.membership?.subscribed == true
                val action = @Composable { Text(if (joined) "Leave" else "Join") }
                if (joined) OutlinedButton(onClick = { header.toggleMembership(onNeedSignIn) }, enabled = !busy && community != null,
                    modifier = Modifier.testTag("membership")) { action() }
                else Button(onClick = { header.toggleMembership(onNeedSignIn) }, enabled = !busy && community != null,
                    modifier = Modifier.testTag("membership")) { action() }
            }
            community?.description?.takeIf { it.isNotBlank() }?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
            community?.membership?.takeIf { it.isModerator }?.let {
                Text("You are ${if (it.role == "owner") "the owner" else "a moderator"} of this community",
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary)
            }
            headerError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
        SortBar(sort, window, { sort = it }, { window = it })
        PostList(
            state = state, signedIn = me != null, onRefresh = list::refresh, onLoadMore = list::loadMore,
            onVote = list::vote, onOpen = onOpenPost, onOpenCommunity = null,
            emptyText = "No posts in c/$slug yet. Be the first to post.",
        )
    }
}

// ---------------- create ----------------

@Composable
fun CreateCommunityScreen(container: AppContainer, onCreated: (String) -> Unit) {
    var slug by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var description by rememberSaveable { mutableStateOf("") }
    var busy by rememberSaveable { mutableStateOf(false) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedTextField(slug, { slug = it.lowercase().filter { c -> c.isLetterOrDigit() || c == '_' }.take(21); error = null },
            label = { Text("Name (a-z, 0-9, _), shown as c/name") }, singleLine = true,
            modifier = Modifier.fillMaxWidth().testTag("community_slug"))
        OutlinedTextField(name, { name = it.take(100) }, label = { Text("Display title (optional)") }, singleLine = true,
            modifier = Modifier.fillMaxWidth())
        OutlinedTextField(description, { description = it.take(5000) }, label = { Text("Description") }, minLines = 3,
            modifier = Modifier.fillMaxWidth())
        Text("You will be the owner and first moderator. Community rules can be added later.",
            style = MaterialTheme.typography.labelSmall)
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(
            enabled = !busy && slug.length >= 3, modifier = Modifier.fillMaxWidth().testTag("community_submit"),
            onClick = {
                busy = true
                scope.launch {
                    try {
                        val c = container.requireApi().createCommunity(slug, name, description)
                        container.markContentChanged()
                        onCreated(c.slug)
                    } catch (e: Exception) {
                        if (e is kotlinx.coroutines.CancellationException) throw e
                        error = e.userMessage()
                    } finally {
                        busy = false
                    }
                }
            },
        ) { Text("Create community") }
    }
}
