import org.gradle.api.Project
import org.gradle.api.file.RegularFile

fun Project.projectFile(path: String): RegularFile = layout.projectDirectory.file(path)
