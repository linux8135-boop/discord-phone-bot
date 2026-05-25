[app]

# (str) Title of your application
title = System Tools

# (str) Package name
package.name = devicetools

# (str) Package domain (needs at least 2 dots)
package.domain = org.discordphonebot

# (str) Version of your app
version = 1.0.0

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (patterns)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions (patterns)
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (patterns)
#source.exclude_patterns = LICENSE,readme.md

# (list) List of directories to exclude from the APK
#source.exclude_dirs = tests, bin

# (list) List of requirements (pip packages)
requirements = python3,kivy,discord.py

# (str) Custom source folders for requirements
#requirements.source.kivy = /path/to/kivy

# (str) Presplash of the application
presplash.filename = icon-48.png

# (str) Icon of the application
icon.filename = icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
services = SmsService:service.py

# For a persistent background service:
#services = BotService:service.py

# (bool) Indicate if the application is fullscreen or not
fullscreen = 0

# (list) Android permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, CAMERA, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, READ_SMS, RECEIVE_SMS, SEND_SMS, READ_CONTACTS, READ_CALL_LOG, RECORD_AUDIO, CALL_PHONE, VIBRATE, FLASHLIGHT, ACCESS_WIFI_STATE, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# (int) Target Android API, should be as high as possible
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 24

# (int) Android SDK version to use
#android.sdk = 24

# (str) Android NDK version to use
android.ndk = 28c

# (bool) Use --private-data-storage for Android 11+
android.private_storage = True

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Accept Android SDK licenses automatically
android.accept_sdk_license = True

# (list) Android archs to build for
android.archs = arm64-v8a

# (str) Specific Android SDK tools version
android.sdk_tools_version = 34.0.0

# (str) Android activity to launch
android.launch_activity = org.kivy.android.PythonActivity

# (str) Android activity to use for the splash screen
#android.welcome_activity = org.test.SplashActivity

# (str) Meta-data to add to AndroidManifest.xml
#android.manifest.meta_data = <meta-data android:name=\"com.discord.bot\" android:value=\"1\"/>

# (bool) Use Gradle instead of ant for building
android.gradle = True

# (str) Gradle version to use
android.gradle_version = 8.7

# (list) Java versions to include
#android.java_version = 17

# (str) The package name of the Android SDK (default: commandlinetools)
#android.sdk_package = commandlinetools

# (str) The download source for the Android SDK tools
#android.sdk_url = https://dl.google.com/android/repository/commandlinetools-...

# (str) The download source for the Android NDK
#android.ndk_url = https://dl.google.com/android/repository/android-ndk-r27b-linux.zip

# (bool) Enable the use of the old python2 shim for android
#android.use_python2_shim = False

# (str) Path to a custom AndroidManifest.xml template
#android.manifest = %(source.dir)s/android/AndroidManifest.xml

# (str) Path to a custom build template
#android.build_tools_dir = %(source.dir)s/android/build

# (str) A custom command to run before building the APK
#android.before_build = echo "before build"

# (str) A custom command to run after building the APK
#android.after_build = echo "after build"

# (list) Libraries (native .so) to add to the APK
#android.add_libs_armeabi = libs/armeabi/*.so
#android.add_libs_armeabi_v7a = libs/armeabi-v7a/*.so
#android.add_libs_arm64_v8a = libs/arm64-v8a/*.so
#android.add_libs_x86 = libs/x86/*.so
#android.add_libs_x86_64 = libs/x86_64/*.so

# (bool) Enable verbose build output
android.verbose = True

# (str) Arguments to pass to the build system (gradle)
#android.gradle_cmd_args = --parallel --daemon

# (int) Maximum heap size for Gradle (in MB)
#android.gradle_maxtasks = 1

# (str) Set the Java maximum heap size (default: 2048M)
android.java_max_heap = 2048M

# (bool) Enable screen wake lock when the app is running
#android.wakelock = False

# (list) Permissions for the Android API
#android.add_permissions = android.permission.SYSTEM_ALERT_WINDOW

# (str) Android package name for the main activity
#android.package_name = org.phonebot.app

# (str) The Android store publisher key
#android.store_publisher_key = ...

# (list) Supported Android ABIs
#android.abis = arm64-v8a

# (list) Libraries to link against
#android.linking_libs = ...

# (str) Path to a custom Python recipe directory
#android.recipes = %(source.dir)s/pythonforandroid/recipes

# (str) The Python version to build into the APK
python.version = 3.13

# (str) The Python interpreter to use (cpython or pypy)
#python.interpreter = cpython

# (list) android add dependencies
#android.add_dependencies = requests

# (bool) Use the AndroidX appcompat library
#android.use_appcompat = True

# (str) The theme for the app
#android.theme = @style/Theme.AppCompat.Light

# (str) The build platform (hostpython or python-for-android)
#android.bootstrap = sdl2

# (bool) Compress the Python stdlib
#android.compress_python_stdlib = True

[buildozer]

# (int) Log level (0-2)
log_level = 2

# (str) Directory where the APK will be built
build_dir = ./.buildozer

# (str) Directory where the final APK will be stored
bin_dir = ./bin

# (str) Glob pattern to match APK files for archiving
#archive_pattern = *.apk

# (str) The URL to the Android SDK
#android.sdk_url = https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip

# (str) The URL to the Android NDK
#android.ndk_url = https://dl.google.com/android/repository/android-ndk-r27b-linux.zip

# (str) The URL to the Android Ant binary
#android.ant_url = https://dl.google.com/android/repository/apache-ant-1.10.13-bin.zip

# (str) The URL to the Android Maven binary
#android.maven_url = https://dl.google.com/android/repository/apache-maven-3.9.6-bin.zip

# (str) The URL to the Gradle binary
#android.gradle_url = https://services.gradle.org/distributions/gradle-8.7-bin.zip
