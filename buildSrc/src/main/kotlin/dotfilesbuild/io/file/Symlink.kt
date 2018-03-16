package dotfilesbuild.io.file

import org.gradle.api.DefaultTask
import org.gradle.api.InvalidUserDataException
import org.gradle.api.file.ProjectLayout
import org.gradle.api.file.RegularFile
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files
import javax.inject.Inject

// Only supports files right now
open class Symlink @Inject constructor(
    projectLayout: ProjectLayout
) : DefaultTask() {

  /**
   * The source file of the link.
   */
  @get:InputFile
  val source: RegularFileProperty = projectLayout.fileProperty()

  /**
   * The destination where the link will be created.
   */
  @get:OutputFile
  val destination: RegularFileProperty = projectLayout.fileProperty()

  @TaskAction
  fun createLink() {
    val sourcePath = source.asFile.get().toPath().toAbsolutePath()
    val destinationPath = destination.asFile.get().toPath().toAbsolutePath()
    if (Files.exists(destinationPath)) {
      if (Files.isSymbolicLink(destinationPath)) {
        logger.info("{} is an existing symbolic link, deleting before recreating", destinationPath)
        Files.delete(destinationPath)
      } else {
        throw InvalidUserDataException("$destinationPath already exists, and isn't a symlink.")
      }
    }
    logger.info("Creating symbolic link at {} for {}", destinationPath, sourcePath)
    Files.createSymbolicLink(destinationPath, sourcePath)
  }
}
