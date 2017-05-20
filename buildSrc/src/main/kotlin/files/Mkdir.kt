package files

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class Mkdir : DefaultTask() {
  @get:InputFile
  var directory: File? = null

  init {
    outputs.upToDateWhen {
      Files.isDirectory(directory!!.toPath())
    }
  }

  @TaskAction
  fun createDir() {
    Files.createDirectories(directory!!.toPath())
  }
}
