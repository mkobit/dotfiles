package dotfilesbuild.io.file

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.InvalidUserDataException
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.file.ProjectLayout
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.OutputDirectory
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import javax.inject.Inject

private val log = KotlinLogging.logger { }
// TODO: figure out how to support symlink of dir and file in same task

open class SymlinkFile @Inject constructor(
    projectLayout: ProjectLayout
) : DefaultTask() {

  /**
   * The source file of the link.
   */
  @get:Input
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
    symlink(sourcePath, destinationPath)
  }
}

open class SymlinkDirectory @Inject constructor(
    projectLayout: ProjectLayout
) : DefaultTask() {

  /**
   * The source directory of the link.
   */
  @get:Internal
  val source: DirectoryProperty = projectLayout.directoryProperty()

  // needed due to https://github.com/gradle/gradle/issues/4861
  @get:Input
  val sourceAsDirFileProvider: Provider<File> = source.asFile

  /**
   * The destination where the link will be created.
   */
  @get:OutputDirectory
  val destination: DirectoryProperty = projectLayout.directoryProperty()

  @TaskAction
  fun createLink() {
    val sourcePath = source.asFile.get().toPath().toAbsolutePath()
    val destinationPath = destination.asFile.get().toPath().toAbsolutePath()
    symlink(sourcePath, destinationPath)
  }
}
private fun symlink(source: Path, destination: Path) {
  if (Files.exists(destination)) {
    if (Files.isSymbolicLink(destination)) {
      log.info("{} is an existing symbolic link, deleting before recreating", destination)
      Files.delete(destination)
    } else {
      throw InvalidUserDataException("$destination already exists, and isn't a symlink.")
    }
  }
  log.info("Creating symbolic link at {} for {}", destination, source)
  Files.createSymbolicLink(destination, source)
}
