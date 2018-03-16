package dotfilesbuild.io.file

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files

open class Mkdir : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  @get:Internal
  val directory: DirectoryProperty = newInputDirectory()

  private val directoryFile: File
    get() = directory.asFile.get()

  init {
    outputs.upToDateWhen {
      Files.isDirectory(directoryFile.toPath())
    }
  }

  @TaskAction
  fun createDir() {
    LOGGER.info { "Creating directory at $directory" }
    Files.createDirectories(directoryFile.toPath())
  }
}
