package dotfilesbuild.io.file

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.InvalidUserDataException
import org.gradle.api.file.FileSystemLocation
import org.gradle.api.file.ProjectLayout
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import javax.inject.Inject

private val log = KotlinLogging.logger { }
// TODO: figure out how to support symlink of dir and file in same task

open class Symlink @Inject constructor(
  projectLayout: ProjectLayout,
  objectFactory: ObjectFactory
) : DefaultTask() {

  init {
    outputs.upToDateWhen {
      Files.isSymbolicLink(destination.get().asFile.toPath())
    }
  }

  /**
   * The source of the link.
   */
  @get:Internal
  val source: Property<FileSystemLocation> = objectFactory.property()

  @get:Input
  private val sourceAsDirFileProvider: Provider<File> = source.map(FileSystemLocation::getAsFile)

  /**
   * The destination where the link will be created.
   */
  @get:Internal
  val destination: Property<FileSystemLocation> = objectFactory.property()

  @TaskAction
  fun createLink() {
    val sourcePath = source.get().asFile.toPath().toAbsolutePath()
    val destinationPath = destination.get().asFile.toPath().toAbsolutePath()
    symlink(sourcePath, destinationPath)
  }

  private fun symlink(source: Path, destination: Path) {
    if (Files.isSymbolicLink(destination)) {
      log.info("{} is an existing symbolic link, deleting before recreating", destination)
      Files.delete(destination)
    } else if (Files.exists(destination, LinkOption.NOFOLLOW_LINKS)) {
      throw InvalidUserDataException("$destination already exists, and isn't a symlink.")
    }
    log.info("Creating symbolic link at {} for {}", destination, source)
    Files.createSymbolicLink(destination, source)
  }
}
