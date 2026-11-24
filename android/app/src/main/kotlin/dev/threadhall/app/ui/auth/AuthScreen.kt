package dev.threadhall.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import dev.threadhall.app.data.AppContainer
import dev.threadhall.app.ui.common.userMessage
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(container: AppContainer, onDone: () -> Unit) {
    var register by rememberSaveable { mutableStateOf(false) }
    var handle by rememberSaveable { mutableStateOf("") }
    // Passwords are deliberately not saved across process death.
    var password by androidx.compose.runtime.remember { mutableStateOf("") }
    var busy by rememberSaveable { mutableStateOf(false) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope { kotlinx.coroutines.Dispatchers.Main.immediate } // UI work stays on the main thread
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        PrimaryTabRow(selectedTabIndex = if (register) 1 else 0) {
            Tab(selected = !register, onClick = { register = false; error = null }, text = { Text("Sign in") })
            Tab(selected = register, onClick = { register = true; error = null }, text = { Text("Create account") },
                modifier = Modifier.testTag("tab_register"))
        }
        Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            if (register) {
                Text(
                    "Pick a handle (3–20 letters, digits, _ or -) and a password of at least 10 characters. " +
                        "Accounts exist only on this server; existing accounts elsewhere are not imported.",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            OutlinedTextField(
                value = handle, onValueChange = { handle = it.trim(); error = null }, label = { Text("Handle") },
                singleLine = true, modifier = Modifier.fillMaxWidth().testTag("handle"),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii, imeAction = ImeAction.Next),
            )
            OutlinedTextField(
                value = password, onValueChange = { password = it; error = null }, label = { Text("Password") },
                singleLine = true, visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
                modifier = Modifier.fillMaxWidth().testTag("password"),
            )
            error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("auth_error")) }
            Button(
                enabled = !busy && handle.isNotBlank() && password.isNotEmpty(),
                modifier = Modifier.fillMaxWidth().testTag("auth_submit"),
                onClick = {
                    busy = true
                    scope.launch {
                        try {
                            val api = container.requireApi()
                            val me = if (register) api.register(handle, password) else api.login(handle, password)
                            password = ""
                            container.onSignedIn(me)
                            onDone()
                        } catch (e: Exception) {
                            if (e is kotlinx.coroutines.CancellationException) throw e
                            error = e.userMessage()
                        } finally {
                            busy = false
                        }
                    }
                },
            ) {
                if (busy) CircularProgressIndicator(strokeWidth = 2.dp) else Text(if (register) "Create account" else "Sign in")
            }
        }
    }
}
