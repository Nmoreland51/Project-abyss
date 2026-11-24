package dev.threadhall.core

import java.io.IOException
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.util.concurrent.TimeUnit

/** Persists the current session's tokens. The Android app backs this with the Keystore. */
interface TokenStore {
    fun load(): Tokens?
    fun save(tokens: Tokens)
    fun clear()
}

class InMemoryTokenStore(private var tokens: Tokens? = null) : TokenStore {
    @Synchronized override fun load(): Tokens? = tokens
    @Synchronized override fun save(tokens: Tokens) { this.tokens = tokens }
    @Synchronized override fun clear() { tokens = null }
}

sealed class ApiException(message: String, cause: Throwable? = null) : Exception(message, cause) {
    /** The server answered with an error envelope. */
    class Http(
        val status: Int,
        val code: String,
        override val message: String,
        val requestId: String?,
        val details: List<ErrorDetail> = emptyList(),
    ) : ApiException(message)

    /** No response (offline, DNS, timeout, TLS). Safe to retry idempotent calls. */
    class Network(cause: IOException) : ApiException(cause.message ?: "Network error", cause)

    /** The response could not be understood (server/client version mismatch). */
    class Protocol(message: String, cause: Throwable? = null) : ApiException(message, cause)
}

sealed interface SessionEvent {
    /** The server rejected the session (revoked/expired); local tokens were cleared. */
    data object SignedOut : SessionEvent
}

class InvalidServerUrl(message: String) : IllegalArgumentException(message)

/**
 * Typed client for the v1 REST API. Thread-safe; one instance per configured server.
 *
 * Authentication: sends the stored access token when present. On a 401 it refreshes once
 * (serialised by a mutex so concurrent calls never race the refresh-token rotation) and retries;
 * if refresh fails the tokens are cleared and [sessionEvents] emits [SessionEvent.SignedOut].
 */
class ThreadhallApi(
    baseUrl: String,
    private val tokenStore: TokenStore,
    private val userAgent: String = "threadhall-core",
    httpClient: OkHttpClient? = null,
) {
    val baseUrl: HttpUrl = parseServerUrl(baseUrl)
    private val http = httpClient ?: defaultHttpClient()
    private val refreshMutex = Mutex()
    private val _sessionEvents = MutableSharedFlow<SessionEvent>(extraBufferCapacity = 4)
    val sessionEvents: SharedFlow<SessionEvent> = _sessionEvents.asSharedFlow()

    val isSignedIn: Boolean get() = tokenStore.load() != null
    val isCleartext: Boolean get() = !this.baseUrl.isHttps

    // ---------------- health & auth ----------------
    suspend fun health(): Health = call("GET", listOf("health", "ready"), deserializer = Health.serializer(), okStatuses = setOf(200, 503))

    suspend fun register(handle: String, password: String): Me =
        authCall(listOf("v1", "auth", "register"), Credentials(handle, password))

    suspend fun login(handle: String, password: String): Me =
        authCall(listOf("v1", "auth", "login"), Credentials(handle, password))

    /** Revokes the session server-side (best effort) and always clears local tokens. */
    suspend fun logout() {
        try {
            if (tokenStore.load() != null) call("POST", listOf("v1", "auth", "logout"), deserializer = Unit.serializer(), retryAuth = false)
        } catch (_: ApiException) {
            // Local sign-out must succeed even when offline or already revoked.
        } finally {
            tokenStore.clear()
        }
    }

    suspend fun me(): Me = call("GET", listOf("v1", "me"), deserializer = Me.serializer())

    suspend fun profile(handle: String): PublicProfile = call("GET", listOf("v1", "users", handle), deserializer = PublicProfile.serializer())

    suspend fun userPosts(handle: String, cursor: String? = null): PostPage =
        call("GET", listOf("v1", "users", handle, "posts"), query = mapOf("cursor" to cursor), deserializer = PostPage.serializer())

    // ---------------- feeds & posts ----------------
    suspend fun feed(scope: FeedScope, sort: PostSort, window: TimeWindow = TimeWindow.DAY, cursor: String? = null, limit: Int = 25): PostPage =
        call(
            "GET", listOf("v1", "feed"),
            query = mapOf("scope" to scope.wire, "sort" to sort.wire, "t" to window.wire, "cursor" to cursor, "limit" to "$limit"),
            deserializer = PostPage.serializer(),
        )

    suspend fun communityPosts(slug: String, sort: PostSort, window: TimeWindow = TimeWindow.DAY, cursor: String? = null, limit: Int = 25): PostPage =
        call(
            "GET", listOf("v1", "communities", slug, "posts"),
            query = mapOf("sort" to sort.wire, "t" to window.wire, "cursor" to cursor, "limit" to "$limit"),
            deserializer = PostPage.serializer(),
        )

    suspend fun post(id: String): Post = call("GET", listOf("v1", "posts", id), deserializer = Post.serializer())

    suspend fun createTextPost(community: String, title: String, body: String?, idempotencyKey: String): Post =
        call("POST", listOf("v1", "posts"), body = encode(NewPost(community, "text", title, body?.ifBlank { null }, null)),
            idempotencyKey = idempotencyKey, deserializer = Post.serializer())

    suspend fun createLinkPost(community: String, title: String, url: String, idempotencyKey: String): Post =
        call("POST", listOf("v1", "posts"), body = encode(NewPost(community, "link", title, null, url)),
            idempotencyKey = idempotencyKey, deserializer = Post.serializer())

    suspend fun editPostBody(id: String, body: String): Post =
        call("PATCH", listOf("v1", "posts", id), body = encode(EditBody(body)), deserializer = Post.serializer())

    suspend fun deletePost(id: String): Unit = call("DELETE", listOf("v1", "posts", id), deserializer = Unit.serializer())

    suspend fun votePost(id: String, value: Int): VoteResult =
        call("PUT", listOf("v1", "posts", id, "vote"), body = encode(Vote(value)), deserializer = VoteResult.serializer())

    // ---------------- comments ----------------
    suspend fun comments(postId: String, sort: CommentSort = CommentSort.TOP, cursor: String? = null, depth: Int = 8): CommentPage =
        call("GET", listOf("v1", "posts", postId, "comments"),
            query = mapOf("sort" to sort.wire, "cursor" to cursor, "depth" to "$depth"), deserializer = CommentPage.serializer())

    suspend fun commentThread(commentId: String, sort: CommentSort = CommentSort.TOP, depth: Int = 8): CommentNode =
        call("GET", listOf("v1", "comments", commentId), query = mapOf("sort" to sort.wire, "depth" to "$depth"),
            deserializer = CommentNode.serializer())

    suspend fun createComment(postId: String, body: String, parentId: String?, idempotencyKey: String): CommentNode =
        call("POST", listOf("v1", "posts", postId, "comments"), body = encode(NewComment(body, parentId)),
            idempotencyKey = idempotencyKey, deserializer = CommentNode.serializer())

    suspend fun editComment(id: String, body: String): CommentNode =
        call("PATCH", listOf("v1", "comments", id), body = encode(EditBody(body)), deserializer = CommentNode.serializer())

    suspend fun deleteComment(id: String): Unit = call("DELETE", listOf("v1", "comments", id), deserializer = Unit.serializer())

    suspend fun voteComment(id: String, value: Int): VoteResult =
        call("PUT", listOf("v1", "comments", id, "vote"), body = encode(Vote(value)), deserializer = VoteResult.serializer())

    // ---------------- communities ----------------
    suspend fun communities(prefix: String? = null, cursor: String? = null): CommunityPage =
        call("GET", listOf("v1", "communities"), query = mapOf("q" to prefix?.ifBlank { null }, "cursor" to cursor),
            deserializer = CommunityPage.serializer())

    suspend fun community(slug: String): Community = call("GET", listOf("v1", "communities", slug), deserializer = Community.serializer())

    suspend fun createCommunity(slug: String, displayName: String?, description: String): Community =
        call("POST", listOf("v1", "communities"), body = encode(NewCommunity(slug, displayName?.ifBlank { null }, description)),
            deserializer = Community.serializer())

    suspend fun subscribe(slug: String): Community =
        call("PUT", listOf("v1", "communities", slug, "membership"), deserializer = Community.serializer())

    suspend fun unsubscribe(slug: String): Community =
        call("DELETE", listOf("v1", "communities", slug, "membership"), deserializer = Community.serializer())

    suspend fun myCommunities(): List<Community> =
        call("GET", listOf("v1", "me", "communities"), deserializer = ListSerializer(Community.serializer()))

    // ---------------- transport ----------------
    private suspend fun authCall(path: List<String>, credentials: Credentials): Me {
        val res: AuthResponse = call("POST", path, body = encode(credentials), deserializer = AuthResponse.serializer(), sendAuth = false)
        tokenStore.save(res.tokens)
        return res.user
    }

    private suspend fun <T> call(
        method: String,
        path: List<String>,
        query: Map<String, String?> = emptyMap(),
        body: String? = null,
        idempotencyKey: String? = null,
        deserializer: KSerializer<T>,
        sendAuth: Boolean = true,
        retryAuth: Boolean = true,
        okStatuses: Set<Int> = emptySet(),
    ): T {
        val tokensUsed = if (sendAuth) tokenStore.load() else null
        val response = execute(buildRequest(method, path, query, body, idempotencyKey, tokensUsed?.accessToken))
        response.use { resp ->
            val text = resp.body.string()
            if (resp.code == 401 && tokensUsed != null && retryAuth) {
                if (refreshAfterFailure(tokensUsed)) {
                    return call(method, path, query, body, idempotencyKey, deserializer, sendAuth, retryAuth = false, okStatuses)
                }
            }
            if (!resp.isSuccessful && resp.code !in okStatuses) throw httpError(resp, text)
            @Suppress("UNCHECKED_CAST")
            if (deserializer == Unit.serializer()) return Unit as T
            return try {
                json.decodeFromString(deserializer, text)
            } catch (e: Exception) {
                throw ApiException.Protocol("Unexpected response from server (${resp.code})", e)
            }
        }
    }

    /** Returns true if a usable new access token is available for a retry. */
    private suspend fun refreshAfterFailure(failed: Tokens): Boolean = refreshMutex.withLock {
        val current = tokenStore.load() ?: return@withLock false
        if (current.accessToken != failed.accessToken) return@withLock true // refreshed by another caller
        val request = buildRequest("POST", listOf("v1", "auth", "refresh"), emptyMap(), encode(RefreshBody(current.refreshToken)), null, null)
        val resp = try {
            execute(request)
        } catch (e: ApiException.Network) {
            throw e // keep tokens: offline is not a sign-out
        }
        resp.use {
            val text = it.body.string()
            when {
                it.isSuccessful -> {
                    tokenStore.save(json.decodeFromString(Tokens.serializer(), text))
                    true
                }
                it.code == 401 -> {
                    tokenStore.clear()
                    _sessionEvents.tryEmit(SessionEvent.SignedOut)
                    false
                }
                else -> throw httpError(it, text)
            }
        }
    }

    private fun buildRequest(
        method: String,
        path: List<String>,
        query: Map<String, String?>,
        body: String?,
        idempotencyKey: String?,
        accessToken: String?,
    ): Request {
        val url = baseUrl.newBuilder().apply {
            path.forEach { addPathSegment(it) }
            query.forEach { (k, v) -> if (v != null) addQueryParameter(k, v) }
        }.build()
        val requestBody = when {
            body != null -> body.toRequestBody(JSON_MEDIA)
            method in setOf("POST", "PUT", "PATCH") -> "".toRequestBody(JSON_MEDIA)
            else -> null
        }
        return Request.Builder().url(url).method(method, requestBody).apply {
            header("Accept", "application/json")
            header("User-Agent", userAgent)
            accessToken?.let { header("Authorization", "Bearer $it") }
            idempotencyKey?.let { header("Idempotency-Key", it) }
        }.build()
    }

    private suspend fun execute(request: Request): Response = try {
        http.newCall(request).await()
    } catch (e: IOException) {
        throw ApiException.Network(e)
    }

    private fun httpError(resp: Response, text: String): ApiException.Http {
        val env = runCatching { json.decodeFromString(ErrorEnvelope.serializer(), text).error }.getOrNull()
        return ApiException.Http(
            status = resp.code,
            code = env?.code ?: "http_${resp.code}",
            message = env?.message ?: "Server returned HTTP ${resp.code}",
            requestId = env?.requestId ?: resp.header("X-Request-ID"),
            details = env?.details.orEmpty(),
        )
    }

    private inline fun <reified T> encode(value: T): String = json.encodeToString(value)

    companion object {
        private val JSON_MEDIA = "application/json; charset=utf-8".toMediaType()

        val json = Json {
            ignoreUnknownKeys = true
            explicitNulls = false
            encodeDefaults = true
        }

        fun defaultHttpClient(): OkHttpClient = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .writeTimeout(20, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()

        /** Accepts "host:port", "http://host:port", "https://host/"; rejects other schemes. */
        fun parseServerUrl(raw: String): HttpUrl {
            val trimmed = raw.trim().trimEnd('/')
            require(trimmed.isNotEmpty()) { "Server address is empty" }
            val withScheme = if ("://" in trimmed) trimmed else "http://$trimmed"
            val scheme = withScheme.substringBefore("://").lowercase()
            if (scheme != "http" && scheme != "https") throw InvalidServerUrl("Only http:// and https:// servers are supported")
            val url = withScheme.toHttpUrlOrNull() ?: throw InvalidServerUrl("Not a valid server address")
            if (url.querySize > 0 || url.fragment != null) throw InvalidServerUrl("Server address must not contain ? or #")
            return url
        }
    }
}

@Serializable private data class Credentials(val handle: String, val password: String)
@Serializable private data class RefreshBody(@SerialName("refresh_token") val refreshToken: String)
@Serializable private data class NewPost(val community: String, val kind: String, val title: String, val body: String?, val url: String?)
@Serializable private data class NewComment(val body: String, @SerialName("parent_id") val parentId: String?)
@Serializable private data class NewCommunity(val slug: String, @SerialName("display_name") val displayName: String?, val description: String)
@Serializable private data class EditBody(val body: String)
@Serializable private data class Vote(val value: Int)

private suspend fun Call.await(): Response = suspendCancellableCoroutine { cont: CancellableContinuation<Response> ->
    enqueue(object : Callback {
        override fun onFailure(call: Call, e: IOException) {
            if (!cont.isCancelled) cont.resumeWithException(e)
        }

        override fun onResponse(call: Call, response: Response) {
            cont.resume(response) { _, value, _ -> value.close() }
        }
    })
    cont.invokeOnCancellation { runCatching { cancel() } }
}
