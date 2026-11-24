package dev.threadhall.core

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Mirrors contracts/openapi.json (API v1). Unknown fields are ignored so additive server changes
// do not break older clients.

@Serializable
data class UserRef(val id: String, val handle: String)

@Serializable
data class Me(
    val id: String,
    val handle: String,
    @SerialName("display_name") val displayName: String? = null,
    val bio: String? = null,
    @SerialName("post_karma") val postKarma: Long = 0,
    @SerialName("comment_karma") val commentKarma: Long = 0,
    @SerialName("created_at") val createdAt: String,
    @SerialName("is_admin") val isAdmin: Boolean = false,
)

@Serializable
data class PublicProfile(
    val id: String,
    val handle: String,
    @SerialName("display_name") val displayName: String? = null,
    val bio: String? = null,
    @SerialName("post_karma") val postKarma: Long = 0,
    @SerialName("comment_karma") val commentKarma: Long = 0,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class Tokens(
    @SerialName("access_token") val accessToken: String,
    @SerialName("access_expires_at") val accessExpiresAt: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("refresh_expires_at") val refreshExpiresAt: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("token_type") val tokenType: String = "Bearer",
)

@Serializable
data class AuthResponse(val user: Me, val tokens: Tokens)

@Serializable
data class CommunityRule(val title: String, val description: String = "")

@Serializable
data class MembershipInfo(val subscribed: Boolean, val role: String) {
    val isModerator: Boolean get() = role == "moderator" || role == "owner"
}

@Serializable
data class Community(
    val id: String,
    val slug: String,
    @SerialName("display_name") val displayName: String,
    val description: String = "",
    val rules: List<CommunityRule> = emptyList(),
    @SerialName("subscriber_count") val subscriberCount: Int = 0,
    @SerialName("created_at") val createdAt: String,
    val membership: MembershipInfo? = null,
)

@Serializable
data class CommunityRef(val id: String, val slug: String, @SerialName("display_name") val displayName: String)

@Serializable
data class CommunityPage(val items: List<Community>, @SerialName("next_cursor") val nextCursor: String? = null)

@Serializable
data class Post(
    val id: String,
    val community: CommunityRef,
    val author: UserRef? = null,
    val origin: String = "local",
    val kind: String,
    val title: String,
    val body: String? = null,
    val url: String? = null,
    @SerialName("url_domain") val urlDomain: String? = null,
    val flair: String? = null,
    val state: String,
    val score: Int,
    @SerialName("comment_count") val commentCount: Int,
    @SerialName("created_at") val createdAt: String,
    @SerialName("edited_at") val editedAt: String? = null,
    @SerialName("my_vote") val myVote: Int = 0,
    val permalink: String,
) {
    val isVisible: Boolean get() = state == "visible"
}

@Serializable
data class PostPage(
    val items: List<Post>,
    @SerialName("next_cursor") val nextCursor: String? = null,
    val sort: String,
    @SerialName("time_window") val timeWindow: String,
    val scope: String,
    @SerialName("ranking_version") val rankingVersion: String,
)

@Serializable
data class CommentNode(
    val id: String,
    @SerialName("post_id") val postId: String,
    @SerialName("parent_id") val parentId: String? = null,
    val author: UserRef? = null,
    val body: String? = null,
    val depth: Int,
    val state: String,
    val score: Int,
    @SerialName("reply_count") val replyCount: Int,
    @SerialName("created_at") val createdAt: String,
    @SerialName("edited_at") val editedAt: String? = null,
    @SerialName("my_vote") val myVote: Int = 0,
    val replies: List<CommentNode> = emptyList(),
    @SerialName("more_replies") val moreReplies: Int = 0,
) {
    val isVisible: Boolean get() = state == "visible"
}

@Serializable
data class CommentPage(
    val items: List<CommentNode>,
    @SerialName("next_cursor") val nextCursor: String? = null,
    val sort: String,
)

@Serializable
data class VoteResult(@SerialName("target_id") val targetId: String, val score: Int, @SerialName("my_vote") val myVote: Int)

@Serializable
data class Health(val status: String, val checks: Map<String, String> = emptyMap(), @SerialName("api_version") val apiVersion: String? = null)

@Serializable
internal data class ErrorBody(
    val code: String,
    val message: String,
    @SerialName("request_id") val requestId: String? = null,
    val details: List<ErrorDetail>? = null,
)

@Serializable
data class ErrorDetail(val field: String? = null, val message: String)

@Serializable
internal data class ErrorEnvelope(val error: ErrorBody)

enum class FeedScope(val wire: String) { HOME("home"), ALL("all") }

enum class PostSort(val wire: String, val label: String) {
    HOT("hot", "Hot"), NEW("new", "New"), TOP("top", "Top"), CONTROVERSIAL("controversial", "Controversial")
}

enum class TimeWindow(val wire: String, val label: String) {
    HOUR("hour", "Past hour"), DAY("day", "Today"), WEEK("week", "This week"),
    MONTH("month", "This month"), YEAR("year", "This year"), ALL("all", "All time")
}

enum class CommentSort(val wire: String, val label: String) { TOP("top", "Top"), NEW("new", "New"), OLD("old", "Old") }
