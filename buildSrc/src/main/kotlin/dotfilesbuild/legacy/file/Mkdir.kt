package dotfilesbuild.legacy.file

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files
import javax.inject.Inject

open class Mkdir @Inject constructor(
  objectFactory: ObjectFactory
) : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  @get:Internal
  val directory: DirectoryProperty = objectFactory.directoryProperty()

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
