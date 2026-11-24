package dev.threadhall.app.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.core.content.edit
import dev.threadhall.core.ThreadhallApi
import dev.threadhall.core.TokenStore
import dev.threadhall.core.Tokens
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Session tokens encrypted with an AES-256-GCM key held in the Android Keystore (non-exportable).
 * Only ciphertext is written to app-private SharedPreferences, which are excluded from backup.
 * If the key becomes unusable (e.g. device lock-screen reset) the session is dropped and the
 * user signs in again; tokens are never stored in plaintext as a fallback.
 */
class KeystoreTokenStore(context: Context) : TokenStore {
    private val prefs = context.getSharedPreferences("session", Context.MODE_PRIVATE)
    @Volatile private var cached: Tokens? = null
    @Volatile private var loaded = false

    @Synchronized
    override fun load(): Tokens? {
        if (loaded) return cached
        cached = prefs.getString(KEY_BLOB, null)?.let { blob ->
            runCatching { ThreadhallApi.json.decodeFromString(Tokens.serializer(), decrypt(blob)) }
                .getOrElse { prefs.edit { remove(KEY_BLOB) }; null }
        }
        loaded = true
        return cached
    }

    @android.annotation.SuppressLint("ApplySharedPref")
    @Synchronized
    override fun save(tokens: Tokens) {
        val blob = encrypt(ThreadhallApi.json.encodeToString(Tokens.serializer(), tokens))
        // commit = true: the new refresh token must be durable before the call returns, otherwise a
        // crash right after rotation would leave only the (now invalid) previous token on disk.
        prefs.edit(commit = true) { putString(KEY_BLOB, blob) }
        cached = tokens
        loaded = true
    }

    @android.annotation.SuppressLint("ApplySharedPref")
    @Synchronized
    override fun clear() {
        prefs.edit(commit = true) { remove(KEY_BLOB) }
        cached = null
        loaded = true
    }

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (ks.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        gen.init(
            KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build(),
        )
        return gen.generateKey()
    }

    private fun encrypt(plain: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.ENCRYPT_MODE, key()) }
        val out = cipher.iv + cipher.doFinal(plain.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(out, Base64.NO_WRAP)
    }

    private fun decrypt(blob: String): String {
        val raw = Base64.decode(blob, Base64.NO_WRAP)
        val iv = raw.copyOfRange(0, IV_BYTES)
        val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, iv)) }
        return String(cipher.doFinal(raw.copyOfRange(IV_BYTES, raw.size)), Charsets.UTF_8)
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val ALIAS = "threadhall_session_v1"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val IV_BYTES = 12
        const val KEY_BLOB = "tokens_v1"
    }
}
