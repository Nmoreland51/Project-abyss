package dev.threadhall.app

import androidx.compose.ui.test.SemanticsNodeInteraction
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToNode
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.printToString
import androidx.compose.ui.test.SemanticsMatcher
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import dev.threadhall.core.InMemoryTokenStore
import dev.threadhall.core.PostSort
import dev.threadhall.core.ThreadhallApi
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import java.util.UUID

/**
 * Drives the REAL app UI (MainActivity, Compose screens, view models, network client) on the JVM
 * via Robolectric against a REAL running server. "Device A" is the app UI; "device B" is a second
 * independent client using the same shipped client library. This is not a substitute for a
 * physical-device test (no real GPU, Keystore or radio), which remains a release gate.
 *   LIVE_BASE_URL=http://localhost:8000 ./gradlew :app:testDebugUnitTest
 */
@RunWith(AndroidJUnit4::class)
@Config(application = UiTestApp::class, sdk = [36], qualifiers = "w411dp-h914dp-xxhdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
class LiveUiFlowTest {
    @get:Rule val ui = createAndroidComposeRule<MainActivity>()
    private val base = System.getenv("LIVE_BASE_URL").orEmpty()

    private fun waitFor(matcher: SemanticsMatcher, timeout: Long = 20_000): SemanticsNodeInteraction {
        try {
            ui.waitUntil(timeout) { ui.onAllNodes(matcher, useUnmergedTree = true).fetchSemanticsNodes().isNotEmpty() }
        } catch (e: androidx.compose.ui.test.ComposeTimeoutException) {
            // Make failures diagnosable: dump what was actually on screen.
            println("UI TREE when waiting for ${matcher.description}:\n" + ui.onRoot(useUnmergedTree = true).printToString())
            throw e
        }
        return ui.onAllNodes(matcher, useUnmergedTree = true)[0]
    }

    private fun waitForTag(tag: String) = waitFor(hasTestTag(tag))
    private fun waitForText(text: String, substring: Boolean = false) = waitFor(hasText(text, substring = substring))

    @Test fun twoAccountsThroughTheAppUi() {
        org.robolectric.shadows.ShadowLog.stream = System.out
        assumeTrue("LIVE_BASE_URL not set; live UI test skipped", base.isNotBlank())
        val tag = UUID.randomUUID().toString().take(6)
        val password = "ui-${UUID.randomUUID()}"
        val annHandle = "ui_ann_$tag"
        val slug = "ui_$tag"
        val title = "Hello from the app UI $tag"

        // First run: connect to the server.
        waitForTag("server_url").performTextInput(base)
        ui.onNodeWithTag("connect").performClick()
        waitForTag("tab_home")
        // Anonymous Home is the normal feed (no archive/date picker); sign up from Profile.
        ui.onNodeWithTag("tab_profile").performClick()
        waitForTag("profile_sign_in").performClick()
        waitForTag("tab_register").performClick()
        ui.onNodeWithTag("handle").performTextInput(annHandle)
        ui.onNodeWithTag("password").performTextInput(password)
        ui.onNodeWithTag("auth_submit").performClick()
        waitForText("u/$annHandle")

        // Create a community, then a post in it.
        ui.onNodeWithTag("tab_communities").performClick()
        waitForTag("create_community").performClick()
        waitForTag("community_slug").performTextInput(slug)
        ui.onNodeWithTag("community_submit").performClick()
        waitForText("Leave")
        ui.onNodeWithTag("fab_new_post").performClick()
        waitForTag("post_title").performTextInput(title)
        ui.onNodeWithTag("post_body").performTextInput("Posted through the Compose UI.")
        ui.onNodeWithTag("post_submit").performClick()
        waitForText("No comments yet. Start the discussion.")

        // Device B: a separate account on its own client joins and comments.
        val deviceB = ThreadhallApi(base, InMemoryTokenStore(), "live-ui-device-b")
        val ben = runBlocking { deviceB.register("ui_ben_$tag", password) }
        val post = runBlocking {
            deviceB.subscribe(slug)
            deviceB.communityPosts(slug, PostSort.NEW).items.single { it.title == title }
        }
        val benComment = runBlocking { deviceB.createComment(post.id, "Ben replying from another device", null, UUID.randomUUID().toString()) }
        runBlocking { deviceB.votePost(post.id, 1) }

        // Device A reopens the thread and sees Ben's comment, replies to it and upvotes it.
        ui.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        waitForText(title).performClick()
        waitForText("Ben replying from another device")
        ui.onNodeWithTag("reply_${benComment.id}").performClick()
        waitForTag("reply_body").performTextInput("Ann answering in the app")
        ui.onNodeWithTag("reply_submit").performClick()
        waitForText("Ann answering in the app")
        ui.onNode(hasContentDescription("Upvote comment") and hasAnyAncestor(hasTestTag("comment_${benComment.id}")), useUnmergedTree = true)
            .performClick()
        waitFor(hasContentDescription("Remove upvote") and hasAnyAncestor(hasTestTag("comment_${benComment.id}")))

        // Server state agrees with what the UI showed.
        runBlocking {
            val thread = deviceB.comments(post.id).items.single()
            assertEquals(benComment.id, thread.id)
            assertEquals("Ann answering in the app", thread.replies.single().body)
            assertEquals(annHandle, thread.replies.single().author?.handle)
            assertEquals(1, thread.score)
            assertEquals(1L, deviceB.me().commentKarma)
            assertEquals(ben.id, deviceB.me().id)
        }

        // Profile shows karma from Ben's vote after a refresh.
        ui.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        ui.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        waitForTag("tab_profile").performClick()
        waitForText("Refresh").performClick()
        waitForText("1 post karma", substring = true)

        // Persisted state (server address + session tokens) is enough for a fresh client to resume.
        // The AppContainer restore path itself is covered by ColdStartTest.
        val app = ApplicationProvider.getApplicationContext<UiTestApp>()
        val resumed = ThreadhallApi(dev.threadhall.app.data.ServerConfigStore(app).baseUrl!!, app.tokens)
        assertEquals(annHandle, runBlocking { resumed.me() }.handle)
    }
}
