import org.gradle.api.Project
import java.io.File

internal val userHome = System.getProperty("user.home")

fun Project.homeFile(filename: Any): File = project.file("$userHome/$filename")

fun Project.projectFile(relativePath: Any): File = project.file("$rootDir/$relativePath")
