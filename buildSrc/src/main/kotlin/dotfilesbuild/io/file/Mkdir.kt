package dotfilesbuild.io.file

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class Mkdir : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  var directoryProvider: Directory? = null

  @get:Input
  val directory: File?
    get() = directoryProvider?.asFile

  init {
    outputs.upToDateWhen {
      Files.isDirectory(directory!!.toPath())
    }
  }

  @TaskAction
  fun createDir() {
    LOGGER.info { "Creating directory at $directory" }
    Files.createDirectories(directory!!.toPath())
  }
}
