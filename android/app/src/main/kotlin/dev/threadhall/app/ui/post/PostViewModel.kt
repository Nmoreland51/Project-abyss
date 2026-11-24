package dev.threadhall.app.ui.post

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.needsSignIn
import dev.threadhall.app.ui.common.userMessage
import dev.threadhall.core.CommentNode
import dev.threadhall.core.CommentSort
import dev.threadhall.core.Post
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ThreadState(
    val post: Post? = null,
    val roots: List<CommentNode> = emptyList(),
    val nextCursor: String? = null,
    val sort: CommentSort = CommentSort.TOP,
    val loading: Boolean = true,
    val loadingMoreRoots: Boolean = false,
    val error: String? = null,
    val collapsed: Set<String> = emptySet(),
    val pending: Set<String> = emptySet(),
    val deleted: Boolean = false,
)

/** One rendered line of the flattened, bounded comment tree. */
sealed interface ThreadLine {
    val key: String
    data class Comment(val node: CommentNode, val collapsed: Boolean) : ThreadLine { override val key = node.id }
    data class More(val parentId: String, val count: Int, val depth: Int) : ThreadLine { override val key = "more-$parentId" }
}

fun flatten(nodes: List<CommentNode>, collapsed: Set<String>, out: MutableList<ThreadLine> = mutableListOf()): List<ThreadLine> {
    for (n in nodes) {
        val isCollapsed = n.id in collapsed
        out += ThreadLine.Comment(n, isCollapsed)
        if (!isCollapsed) {
            flatten(n.replies, collapsed, out)
            if (n.moreReplies > 0) out += ThreadLine.More(n.id, n.moreReplies, n.depth + 1)
        }
    }
    return out
}

private fun List<CommentNode>.mapNode(id: String, f: (CommentNode) -> CommentNode): List<CommentNode> =
    map { if (it.id == id) f(it) else if (it.replies.isEmpty()) it else it.copy(replies = it.replies.mapNode(id, f)) }

class PostViewModel(
    private val container: AppContainer,
    private val postId: String,
    private val onNeedSignIn: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(ThreadState())
    val state: StateFlow<ThreadState> = _state.asStateFlow()

    init { load() }

    fun setSort(sort: CommentSort) { _state.update { it.copy(sort = sort) }; load() }

    fun load() {
        _state.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            try {
                val api = container.requireApi()
                val post = api.post(postId)
                val page = api.comments(postId, _state.value.sort)
                _state.update { it.copy(post = post, roots = page.items, nextCursor = page.nextCursor, loading = false) }
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                _state.update { it.copy(loading = false, error = e.userMessage()) }
            }
        }
    }

    fun loadMoreRoots() {
        val s = _state.value
        val cursor = s.nextCursor ?: return
        if (s.loadingMoreRoots) return
        _state.update { it.copy(loadingMoreRoots = true) }
        viewModelScope.launch {
            try {
                val page = container.requireApi().comments(postId, s.sort, cursor)
                _state.update { cur ->
                    val seen = cur.roots.mapTo(HashSet()) { it.id }
                    cur.copy(roots = cur.roots + page.items.filter { it.id !in seen }, nextCursor = page.nextCursor, loadingMoreRoots = false)
                }
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                _state.update { it.copy(loadingMoreRoots = false) }
                container.notify(e.userMessage())
            }
        }
    }

    /** "Continue this thread": fetch the subtree under [commentId] and splice it in. */
    fun loadReplies(commentId: String) = guarded("more-$commentId") {
        val subtree = container.requireApi().commentThread(commentId, _state.value.sort)
        _state.update { it.copy(roots = it.roots.mapNode(commentId) { subtree }) }
    }

    fun toggleCollapse(id: String) = _state.update {
        it.copy(collapsed = if (id in it.collapsed) it.collapsed - id else it.collapsed + id)
    }

    fun votePost(value: Int) = guarded("post") {
        val r = container.requireApi().votePost(postId, value)
        _state.update { it.copy(post = it.post?.copy(score = r.score, myVote = r.myVote)) }
    }

    fun voteComment(id: String, value: Int) = guarded(id) {
        val r = container.requireApi().voteComment(id, value)
        _state.update { it.copy(roots = it.roots.mapNode(id) { n -> n.copy(score = r.score, myVote = r.myVote) }) }
    }

    /** Server-confirmed reply. Returns null on success, or an error message for the composer. */
    suspend fun reply(parentId: String?, body: String, idempotencyKey: String): String? = try {
        val created = container.requireApi().createComment(postId, body, parentId, idempotencyKey)
        _state.update { s ->
            val roots = if (parentId == null) listOf(created) + s.roots.filter { it.id != created.id }
            else s.roots.mapNode(parentId) { p ->
                if (p.replies.any { it.id == created.id }) p
                else p.copy(replies = listOf(created) + p.replies, replyCount = p.replyCount + 1)
            }
            s.copy(roots = roots, post = s.post?.copy(commentCount = s.post.commentCount + 1), collapsed = s.collapsed - (parentId ?: ""))
        }
        null
    } catch (e: Exception) {
        if (e is CancellationException) throw e
        if (e.needsSignIn()) onNeedSignIn()
        e.userMessage()
    }

    fun deleteComment(id: String) = guarded(id) {
        container.requireApi().deleteComment(id)
        _state.update { s -> s.copy(roots = s.roots.mapNode(id) { it.copy(state = "deleted", body = "[deleted]", author = null) }) }
    }

    fun deletePost() = guarded("post") {
        container.requireApi().deletePost(postId)
        container.markContentChanged()
        _state.update { it.copy(deleted = true) }
    }

    private fun guarded(key: String, block: suspend () -> Unit) {
        if (key in _state.value.pending) return
        _state.update { it.copy(pending = it.pending + key) }
        viewModelScope.launch {
            try {
                block()
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                if (e.needsSignIn()) onNeedSignIn() else container.notify(e.userMessage())
            } finally {
                _state.update { it.copy(pending = it.pending - key) }
            }
        }
    }
}
