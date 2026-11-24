plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

// Release signing comes from the owner's environment; the key never lives in the repository.
//   THREADHALL_KEYSTORE=/path/release.jks THREADHALL_KEYSTORE_PASSWORD=... THREADHALL_KEY_ALIAS=...
//   THREADHALL_KEY_PASSWORD=... ./gradlew :app:assembleRelease
val releaseKeystore: String? = System.getenv("THREADHALL_KEYSTORE")

android {
    namespace = "dev.threadhall.app"
    // Compose 1.13 / Navigation 2.10 require compiling against API 37.1+. targetSdk stays 36
    // (runtime behaviour), minSdk 26 (Android 8.0) decides which devices can install.
    compileSdk {
        version = release(37) { minorApiLevel = 2 }
    }

    defaultConfig {
        applicationId = "dev.threadhall.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        // Shared, PUBLIC pilot key so builds from any machine/CI can update each other on a test
        // phone. It provides no security guarantee and must never sign a public release.
        create("pilot") {
            storeFile = rootProject.file("keystore/pilot-debug.jks")
            storePassword = "pilot-debug"
            keyAlias = "pilot"
            keyPassword = "pilot-debug"
        }
        if (releaseKeystore != null) {
            create("release") {
                storeFile = file(releaseKeystore)
                storePassword = System.getenv("THREADHALL_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("THREADHALL_KEY_ALIAS")
                keyPassword = System.getenv("THREADHALL_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        debug {
            // "Pilot" build: debuggable, allows http:// servers on a private LAN, pilot-signed.
            applicationIdSuffix = ".pilot"
            versionNameSuffix = "-pilot"
            signingConfig = signingConfigs.getByName("pilot")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = if (releaseKeystore != null) signingConfigs.getByName("release") else null
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            all {
                it.environment("LIVE_BASE_URL", System.getenv("LIVE_BASE_URL") ?: "")
                it.testLogging { events("passed", "skipped", "failed"); showStandardStreams = true }
            }
        }
    }

    packaging {
        resources.excludes += setOf("META-INF/AL2.0", "META-INF/LGPL2.1", "META-INF/versions/9/OSGI-INF/MANIFEST.MF")
    }

    lint {
        abortOnError = true
        warningsAsErrors = false
    }
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

dependencies {
    implementation(project(":core"))
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons.core)
    implementation(libs.lifecycle.viewmodel.compose)
    implementation(libs.lifecycle.runtime.compose)
    implementation(libs.navigation.compose)
    implementation(libs.kotlinx.coroutines.android)
    debugImplementation(libs.compose.ui.tooling)
    debugImplementation(libs.compose.ui.test.manifest)

    testImplementation(libs.junit)
    testImplementation(libs.robolectric) {
        // Native graphics runtime is optional for these tests (they run in LEGACY graphics mode);
        // excluding it avoids a ~100 MB download that is not needed for semantics-level UI tests.
        exclude(group = "org.robolectric", module = "nativeruntime-dist-compat")
    }
    testImplementation(libs.androidx.test.core)
    testImplementation(libs.androidx.test.ext.junit)
    testImplementation(platform(libs.compose.bom))
    testImplementation(libs.compose.ui.test.junit4)
    testImplementation(libs.kotlinx.coroutines.test)
}
