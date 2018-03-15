import org.gradle.api.Project
import org.gradle.api.file.Directory
import org.gradle.api.file.RegularFile
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.ListProperty

private val userHome: String = System.getProperty("user.home")

val Project.home: Directory
  get() = layout.directoryProperty().run {
    set(this@home.file(userHome))
    get()
  }

@Deprecated("Use the home property instead")
fun Project.home(): Directory = home

fun Project.homeDir(path: String): Directory = home().dir(path)

fun Project.homeFile(path: String): RegularFile = home().file(path)

fun Project.projectFile(path: String): RegularFile = layout.projectDirectory.file(path)

inline fun <reified T> ObjectFactory.listProperty(): ListProperty<T> = listProperty(T::class.java)
