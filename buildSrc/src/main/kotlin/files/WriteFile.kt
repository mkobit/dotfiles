package files

import org.gradle.api.DefaultTask
import org.gradle.api.file.RegularFile
import org.gradle.api.provider.PropertyState
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class WriteFile : DefaultTask() {

  val textState: PropertyState<String> = project.property(String::class.java)
  var destinationProvider: RegularFile? = null

  @get:Input
  var text: String?
    get() = textState.orNull
    set(value) = textState.set(textState)

  @get:OutputFile
  val destination: File?
    get() = destinationProvider?.get()

  @TaskAction
  fun writeText() {
    Files.write(destination!!.toPath(), text!!.toByteArray())
  }
}
