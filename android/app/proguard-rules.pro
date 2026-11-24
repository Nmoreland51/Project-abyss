# kotlinx.serialization: keep generated serializers for API models.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keep,includedescriptorclasses class dev.threadhall.core.**$$serializer { *; }
-keepclassmembers class dev.threadhall.core.** { *** Companion; }
-keepclasseswithmembers class dev.threadhall.core.** { kotlinx.serialization.KSerializer serializer(...); }
# OkHttp ships its own consumer rules.
