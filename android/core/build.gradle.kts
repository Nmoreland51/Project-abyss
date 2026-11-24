// Pure Kotlin/JVM module: API contract models and HTTP client. No Android dependencies, so the
// same code the app ships is exercised by JVM tests against a real running server.
plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

dependencies {
    api(libs.okhttp)
    api(libs.kotlinx.serialization.json)
    api(libs.kotlinx.coroutines.core)
    testImplementation(libs.junit)
    testImplementation(libs.okhttp.mockwebserver)
    testImplementation(libs.kotlinx.coroutines.test)
}

tasks.test {
    // Live tests run only when a server URL is supplied, e.g.
    //   LIVE_BASE_URL=http://localhost:8000 ./gradlew :core:test
    environment("LIVE_BASE_URL", System.getenv("LIVE_BASE_URL") ?: "")
    testLogging {
        events("passed", "skipped", "failed")
        showStandardStreams = true
    }
}
