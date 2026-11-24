package dev.threadhall.core

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.util.UUID

/**
 * Phase 1 gate scenario run through the exact client code the Android app ships, against a REAL
 * running server (no mocks). Two independent clients = two devices with separate token stores.
 * Skipped unless LIVE_BASE_URL is set:  LIVE_BASE_URL=http://localhost:8000 ./gradlew :core:test
 */
class LiveServerTest {
    private val base = System.getenv("LIVE_BASE_URL").orEmpty()

    @Test fun twoAccountsInteractOnTheSameServer() = runBlocking {
        assumeTrue("LIVE_BASE_URL not set; live test skipped", base.isNotBlank())
        val tag = UUID.randomUUID().toString().take(6)
        val password = "live-${UUID.randomUUID()}"
        val deviceA = ThreadhallApi(base, InMemoryTokenStore(), userAgent = "live-test-device-a")
        val deviceB = ThreadhallApi(base, InMemoryTokenStore(), userAgent = "live-test-device-b")
        assertEquals("ok", deviceA.health().status)

        val ann = deviceA.register("live_ann_$tag", password)
        val ben = deviceB.register("live_ben_$tag", password)
        val slug = "live_$tag"
        val created = deviceA.createCommunity(slug, "Live $tag", "Kotlin client live test")
        assertEquals("owner", created.membership?.role)
        assertTrue(deviceB.subscribe(slug).membership?.subscribed == true)

        val key = UUID.randomUUID().toString()
        val post = deviceB.createTextPost(slug, "Ben's post $tag", "from device B", key)
        val retried = deviceB.createTextPost(slug, "Ben's post $tag", "from device B", key)
        assertEquals("retry with the same idempotency key returns the same post", post.id, retried.id)

        val annHome = deviceA.feed(FeedScope.HOME, PostSort.NEW)
        assertTrue("Ann sees Ben's post in Home", annHome.items.any { it.id == post.id })

        val top = deviceA.createComment(post.id, "Hi Ben, from device A", null, UUID.randomUUID().toString())
        val reply = deviceB.createComment(post.id, "Hi Ann!", top.id, UUID.randomUUID().toString())
        assertEquals(1, reply.depth)

        assertEquals(1, deviceA.votePost(post.id, 1).score)
        assertEquals(1, deviceA.votePost(post.id, 1).score) // retry is a no-op
        assertEquals(-1, deviceA.votePost(post.id, -1).score) // reversal
        assertEquals(1, deviceA.votePost(post.id, 1).score)
        assertEquals(1, deviceB.voteComment(top.id, 1).score)

        val thread = deviceB.comments(post.id)
        assertEquals(top.id, thread.items.single().id)
        assertEquals(reply.id, thread.items.single().replies.single().id)
        assertEquals(1, thread.items.single().myVote)

        assertEquals(1L, deviceB.me().postKarma)
        assertEquals(1L, deviceA.me().commentKarma)
        assertEquals(ann.id, deviceA.me().id)
        assertEquals(ben.id, deviceB.me().id)

        // Authorization: device A cannot edit or delete B's post.
        val denied = runCatching { deviceA.editPostBody(post.id, "hijack") }.exceptionOrNull()
        assertTrue(denied is ApiException.Http && denied.status == 403)

        deviceA.logout()
        val afterLogout = runCatching { deviceA.me() }.exceptionOrNull()
        assertTrue(afterLogout is ApiException.Http && afterLogout.status == 401)
        assertTrue("other device stays signed in", deviceB.me().handle == ben.handle)
        println("LIVE OK base=$base post=${post.id} community=$slug")
    }
}
