package dev.threadhall.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.auth.AuthScreen
import dev.threadhall.app.ui.community.CommunitiesScreen
import dev.threadhall.app.ui.community.CommunityScreen
import dev.threadhall.app.ui.community.CreateCommunityScreen
import dev.threadhall.app.ui.feed.FeedScreen
import dev.threadhall.app.ui.feed.PostList
import dev.threadhall.app.ui.feed.PostListViewModel
import dev.threadhall.app.ui.post.CreatePostScreen
import dev.threadhall.app.ui.post.PostScreen
import dev.threadhall.app.ui.profile.ProfileScreen
import dev.threadhall.app.ui.setup.ServerSetupScreen
import dev.threadhall.app.ui.theme.ThreadhallTheme
import dev.threadhall.core.FeedScope

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val container = (application as ThreadhallApp).container
        setContent { ThreadhallRoot(container) }
    }
}

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("home", "Home", Icons.Filled.Home),
    Tab("all", "All", Icons.Filled.Star),
    Tab("communities", "Communities", Icons.AutoMirrored.Filled.List),
    Tab("profile", "Profile", Icons.Filled.Person),
)

@Composable
fun ThreadhallRoot(container: AppContainer) {
    val api by container.api.collectAsStateWithLifecycle()
    ThreadhallTheme {
        Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            if (api == null) {
                Scaffold { pad -> androidx.compose.foundation.layout.Box(Modifier.padding(pad)) { ServerSetupScreen(container, null) {} } }
            } else {
                MainNav(container)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainNav(container: AppContainer) {
    val nav = rememberNavController()
    val entry by nav.currentBackStackEntryAsState()
    val route = entry?.destination?.route ?: "home"
    val me by container.me.collectAsStateWithLifecycle()
    val api by container.api.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(Unit) { container.messages.collect { snackbar.showSnackbar(it) } }

    val topLevel = tabs.any { it.route == route }
    val communitySlug = entry?.arguments?.getString("slug")
    val requireSignIn = { nav.navigate("auth") { launchSingleTop = true } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(titleFor(route, communitySlug), maxLines = 1) },
                navigationIcon = {
                    if (!topLevel) IconButton(onClick = { nav.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        bottomBar = {
            if (topLevel) NavigationBar {
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = route == tab.route,
                        onClick = { nav.navigateTab(tab.route) },
                        icon = { Icon(tab.icon, contentDescription = null) },
                        label = { Text(tab.label) },
                        modifier = Modifier.testTag("tab_${tab.route}"),
                    )
                }
            }
        },
        floatingActionButton = {
            if (route in setOf("home", "all", "community/{slug}")) {
                ExtendedFloatingActionButton(
                    onClick = { if (me == null) requireSignIn() else nav.navigate("submit?community=${communitySlug ?: ""}") },
                    icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                    text = { Text("New post") },
                    modifier = Modifier.testTag("fab_new_post"),
                )
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { pad ->
        NavHost(nav, startDestination = "home", modifier = Modifier.padding(pad)) {
            val openPost = { id: String -> nav.navigate("post/$id") }
            val openCommunity = { slug: String -> nav.navigate("community/$slug") }
            composable("home") {
                FeedScreen(container, FeedScope.HOME, { openPost(it.id) }, openCommunity, requireSignIn) { nav.navigateTab("communities") }
            }
            composable("all") {
                FeedScreen(container, FeedScope.ALL, { openPost(it.id) }, openCommunity, requireSignIn) { nav.navigateTab("communities") }
            }
            composable("communities") {
                CommunitiesScreen(container, openCommunity) { if (me == null) requireSignIn() else nav.navigate("create_community") }
            }
            composable("profile") {
                ProfileScreen(container, onSignIn = requireSignIn, onChangeServer = { nav.navigate("server") },
                    onMyPosts = { nav.navigate("user/$it") })
            }
            composable("community/{slug}", arguments = listOf(navArgument("slug") { type = NavType.StringType })) { e ->
                CommunityScreen(container, e.arguments!!.getString("slug")!!, { openPost(it.id) }, requireSignIn)
            }
            composable("post/{id}", arguments = listOf(navArgument("id") { type = NavType.StringType })) { e ->
                PostScreen(container, e.arguments!!.getString("id")!!, requireSignIn, openCommunity, onDeleted = { nav.popBackStack() })
            }
            composable(
                "submit?community={community}",
                arguments = listOf(navArgument("community") { type = NavType.StringType; defaultValue = "" }),
            ) { e ->
                CreatePostScreen(container, e.arguments?.getString("community")?.ifBlank { null }) { id ->
                    nav.navigate("post/$id") { popUpTo("submit?community={community}") { inclusive = true } }
                }
            }
            composable("create_community") {
                CreateCommunityScreen(container) { slug ->
                    nav.navigate("community/$slug") { popUpTo("create_community") { inclusive = true } }
                }
            }
            composable("auth") { AuthScreen(container) { nav.popBackStack() } }
            composable("server") {
                ServerSetupScreen(container, api?.baseUrl?.toString()) { nav.navigateTab("home") }
            }
            composable("user/{handle}", arguments = listOf(navArgument("handle") { type = NavType.StringType })) { e ->
                val handle = e.arguments!!.getString("handle")!!
                val vm: PostListViewModel = viewModel(key = "user:$handle:${me?.id}") {
                    PostListViewModel(container::requireApi, { a, c -> a.userPosts(handle, c) }, requireSignIn, container::notify,
                        container.contentVersion)
                }
                val state by vm.state.collectAsStateWithLifecycle()
                PostList(state, me != null, vm::refresh, vm::loadMore, vm::vote, { openPost(it.id) }, openCommunity,
                    emptyText = "u/$handle has not posted yet.")
            }
        }
    }
}

private fun NavHostController.navigateTab(route: String) = navigate(route) {
    popUpTo("home") { saveState = true }
    launchSingleTop = true
    restoreState = true
}

private fun titleFor(route: String, slug: String?): String = when (route) {
    "home" -> "Home"
    "all" -> "All"
    "communities" -> "Communities"
    "profile" -> "Profile"
    "community/{slug}" -> "c/${slug ?: ""}"
    "post/{id}" -> "Discussion"
    "submit?community={community}" -> "New post"
    "create_community" -> "New community"
    "auth" -> "Sign in"
    "server" -> "Server"
    "user/{handle}" -> "Posts"
    else -> "Threadhall"
}
