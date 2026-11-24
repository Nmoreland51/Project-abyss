package dev.threadhall.core

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.runBlocking
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import java.util.concurrent.atomic.AtomicInteger

/** Client behaviour against a scripted HTTP server (protocol-level unit tests, not live evidence). */
class ThreadhallApiTest {
    private lateinit var server: MockWebServer

    @Before fun setUp() { server = MockWebServer().also { it.start() } }
    @After fun tearDown() { server.close() }

    private fun tokens(n: Int) = Tokens("at_$n", "2030-01-01T00:00:00Z", "rt_$n", "2030-01-01T00:00:00Z", "sess")

    private val meJson = """{"id":"u1","handle":"ann","post_karma":3,"comment_karma":4,"created_at":"2026-11-24T00:00:00Z","is_admin":false,"future_field":true}"""

    @Test fun parsesServerUrls() {
        assertEquals("http://192.168.1.5:8000/", ThreadhallApi.parseServerUrl("192.168.1.5:8000").toString())
        assertEquals("https://forum.example.org/", ThreadhallApi.parseServerUrl(" https://forum.example.org/ ").toString())
        for (bad in listOf("", "ftp://x.org", "javascript:alert(1)", "http://x.org/?a=b")) {
            try {
                ThreadhallApi.parseServerUrl(bad); fail("accepted $bad")
            } catch (_: IllegalArgumentException) {
            }
        }
    }

    @Test fun errorEnvelopeIsSurfaced() = runBlocking {
        server.enqueue(MockResponse.Builder().code(409)
            .body("""{"error":{"code":"handle_taken","message":"That handle is already taken","request_id":"r1"}}""").build())
        val api = ThreadhallApi(server.url("/").toString(), InMemoryTokenStore())
        try {
            api.register("ann", "long-password-1"); fail("expected error")
        } catch (e: ApiException.Http) {
            assertEquals(409, e.status); assertEquals("handle_taken", e.code); assertEquals("r1", e.requestId)
        }
    }

    @Test fun loginStoresTokensAndSendsBearer() = runBlocking {
        server.enqueue(MockResponse.Builder().code(200).body("""{"user":$meJson,"tokens":${ThreadhallApi.json.encodeToString(Tokens.serializer(), tokens(1))}}""").build())
        server.enqueue(MockResponse.Builder().code(200).body(meJson).build())
        val store = InMemoryTokenStore()
        val api = ThreadhallApi(server.url("/").toString(), store)
        assertEquals("ann", api.login("ann", "pw-pw-pw-pw").handle)
        assertEquals("at_1", store.load()?.accessToken)
        api.me()
        server.takeRequest()
        assertEquals("Bearer at_1", server.takeRequest().headers["Authorization"])
    }

    @Test fun expiredAccessTokenIsRefreshedOnceForConcurrentCalls() = runBlocking {
        val refreshes = AtomicInteger()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                val auth = request.headers["Authorization"]
                return when {
                    request.url.encodedPath == "/v1/auth/refresh" -> {
                        refreshes.incrementAndGet()
                        Thread.sleep(100)
                        MockResponse.Builder().code(200).body(ThreadhallApi.json.encodeToString(Tokens.serializer(), tokens(2))).build()
                    }
                    auth == "Bearer at_2" -> MockResponse.Builder().code(200).body(meJson).build()
                    else -> MockResponse.Builder().code(401).body("""{"error":{"code":"token_expired","message":"expired","request_id":"x"}}""").build()
                }
            }
        }
        val store = InMemoryTokenStore(tokens(1))
        val api = ThreadhallApi(server.url("/").toString(), store)
        val results = (1..5).map { async { api.me() } }.awaitAll()
        assertEquals(5, results.size)
        assertEquals("refresh must be serialised", 1, refreshes.get())
        assertEquals("at_2", store.load()?.accessToken)
    }

    @Test fun rejectedRefreshSignsOut() = runBlocking {
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest) =
                MockResponse.Builder().code(401).body("""{"error":{"code":"unauthorized","message":"revoked","request_id":"x"}}""").build()
        }
        val store = InMemoryTokenStore(tokens(1))
        val api = ThreadhallApi(server.url("/").toString(), store)
        try {
            api.me(); fail("expected 401")
        } catch (e: ApiException.Http) {
            assertEquals(401, e.status)
        }
        assertNull(store.load())
        assertFalse(api.isSignedIn)
    }

    @Test fun offlineIsANetworkErrorAndKeepsTokens() = runBlocking {
        val store = InMemoryTokenStore(tokens(1))
        val url = server.url("/").toString()
        server.close()
        val api = ThreadhallApi(url, store)
        try {
            api.me(); fail("expected network error")
        } catch (_: ApiException.Network) {
        }
        assertTrue("offline must not sign the user out", api.isSignedIn)
    }

    @Test fun idempotencyKeyAndPathEncoding() = runBlocking {
        server.enqueue(MockResponse.Builder().code(201).body(
            """{"id":"c1","post_id":"p1","depth":0,"state":"visible","score":0,"reply_count":0,"created_at":"2026-11-24T00:00:00Z"}"""
        ).build())
        server.enqueue(MockResponse.Builder().code(404).body("""{"error":{"code":"not_found","message":"Community not found","request_id":"x"}}""").build())
        val api = ThreadhallApi(server.url("/").toString(), InMemoryTokenStore(tokens(1)))
        api.createComment("p1", "hi", null, "key-12345678")
        val req = server.takeRequest()
        assertEquals("key-12345678", req.headers["Idempotency-Key"])
        assertEquals("""{"body":"hi"}""", req.body?.utf8()) // nulls omitted; server defaults parent_id to null
        runCatching { api.community("../admin?x=1") }
        assertEquals("/v1/communities/..%2Fadmin%3Fx=1", server.takeRequest().url.encodedPath)
    }
}
