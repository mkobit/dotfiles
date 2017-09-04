package files

import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class Mkdir : DefaultTask() {

  var directoryProvider: Directory? = null

  @get:Input
  val directory: File?
    get() = directoryProvider?.get()

  init {
    outputs.upToDateWhen {
      Files.isDirectory(directory!!.toPath())
    }
  }

  @TaskAction
  fun createDir() {
    logger.info("Creating directory at {}", directory)
    Files.createDirectories(directory!!.toPath())
  }
}
