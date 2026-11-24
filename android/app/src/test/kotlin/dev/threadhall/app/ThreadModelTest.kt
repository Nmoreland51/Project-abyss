package dev.threadhall.app

import dev.threadhall.app.ui.common.compactCount
import dev.threadhall.app.ui.common.relativeAge
import dev.threadhall.app.ui.post.ThreadLine
import dev.threadhall.app.ui.post.flatten
import dev.threadhall.core.CommentNode
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.Instant

class ThreadModelTest {
    private fun node(id: String, depth: Int, replies: List<CommentNode> = emptyList(), more: Int = 0) = CommentNode(
        id = id, postId = "p", parentId = null, body = id, depth = depth, state = "visible", score = 0,
        replyCount = replies.size + more, createdAt = "2026-11-24T00:00:00Z", replies = replies, moreReplies = more,
    )

    @Test fun flattenIsDepthFirstAndRespectsCollapse() {
        val tree = listOf(node("a", 0, listOf(node("a1", 1, listOf(node("a1x", 2)), more = 0), node("a2", 1, more = 3))), node("b", 0))
        assertEquals(listOf("a", "a1", "a1x", "a2", "more-a2", "b"), flatten(tree, emptySet()).map { it.key })
        assertEquals(listOf("a", "b"), flatten(tree, setOf("a")).map { it.key })
        val more = flatten(tree, emptySet()).filterIsInstance<ThreadLine.More>().single()
        assertEquals(3, more.count); assertEquals(2, more.depth)
    }

    @Test fun formatting() {
        val now = Instant.parse("2026-11-24T12:00:00Z")
        assertEquals("now", relativeAge("2026-11-24T11:59:30Z", now))
        assertEquals("5m", relativeAge("2026-11-24T11:55:00+00:00", now))
        assertEquals("3h", relativeAge("2026-11-24T09:00:00Z", now))
        assertEquals("2d", relativeAge("2026-11-22T12:00:00Z", now))
        assertEquals("", relativeAge("garbage", now))
        assertEquals("999", compactCount(999)); assertEquals("1.5k", compactCount(1500)); assertEquals("12k", compactCount(12345))
    }
}
