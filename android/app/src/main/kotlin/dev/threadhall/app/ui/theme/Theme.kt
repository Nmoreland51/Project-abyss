package dev.threadhall.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Original palette (navy / sky / sea-green / rose); deliberately distinct from other services' branding.
private val Navy = Color(0xFF1E3A5F)
private val Sky = Color(0xFF7FB8E6)

@Immutable
data class VoteColors(val up: Color, val down: Color, val neutral: Color)

val LocalVoteColors = staticCompositionLocalOf { VoteColors(Color(0xFF2E8B57), Color(0xFFB5485D), Color.Gray) }

private val Light = lightColorScheme(
    primary = Navy,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD6E6F5),
    onPrimaryContainer = Color(0xFF0B1F33),
    secondary = Color(0xFF3F6E8C),
    background = Color(0xFFF7F8FA),
    surface = Color.White,
    surfaceVariant = Color(0xFFE9EDF1),
    outlineVariant = Color(0xFFD3D9DF),
)

private val Dark = darkColorScheme(
    primary = Sky,
    onPrimary = Color(0xFF0B1F33),
    primaryContainer = Color(0xFF26486E),
    onPrimaryContainer = Color(0xFFD6E6F5),
    secondary = Color(0xFF9CC3DD),
    background = Color(0xFF101418),
    surface = Color(0xFF161B20),
    surfaceVariant = Color(0xFF222A31),
    outlineVariant = Color(0xFF39434C),
)

private val AppTypography = Typography(
    titleMedium = TextStyle(fontSize = 16.sp, lineHeight = 21.sp, fontWeight = FontWeight.SemiBold),
    bodyMedium = TextStyle(fontSize = 14.sp, lineHeight = 20.sp),
    labelSmall = TextStyle(fontSize = 12.sp, lineHeight = 16.sp),
)

@Composable
fun ThreadhallTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    val votes = if (dark) VoteColors(Color(0xFF5FD39A), Color(0xFFE88A9C), Color(0xFF9AA4AE))
    else VoteColors(Color(0xFF237A4B), Color(0xFFB03A52), Color(0xFF6B7681))
    androidx.compose.runtime.CompositionLocalProvider(LocalVoteColors provides votes) {
        MaterialTheme(colorScheme = if (dark) Dark else Light, typography = AppTypography, content = content)
    }
}
