package files

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class WriteFile : DefaultTask() {

  @get:Input
  var text: String? = null

  @get:OutputFile
  var destination: File? = null

  @TaskAction
  fun writeText() {
    Files.write(destination!!.toPath(), text!!.toByteArray())
  }
}
