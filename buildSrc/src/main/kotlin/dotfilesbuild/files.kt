package dotfilesbuild

import org.gradle.api.Project
import org.gradle.api.file.Directory
import org.gradle.api.file.RegularFile

private val userHome: String = System.getProperty("user.home")

val Project.home: Directory
  get() = layout.directoryProperty().run {
    set(this@home.file(userHome))
    get()
  }

fun Project.projectFile(path: String): RegularFile = layout.projectDirectory.file(path)

@Deprecated("superseded", ReplaceWith("home", "dotfilesbuild.home"))
fun Project.homeFile(path: String): RegularFile = home.file(path)
