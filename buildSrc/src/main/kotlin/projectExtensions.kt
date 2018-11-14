import org.gradle.api.Project
import org.gradle.api.file.RegularFile
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.ListProperty

fun Project.projectFile(path: String): RegularFile = layout.projectDirectory.file(path)
