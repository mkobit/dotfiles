package dotfilesbuild.io.file

import arrow.core.Either
import dotfilesbuild.io.file.content.TextEditAction
import org.gradle.api.DefaultTask
import org.gradle.api.file.ProjectLayout
import org.gradle.api.file.RegularFile
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.ListProperty
import org.gradle.api.provider.Property
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.Optional
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.listProperty
import org.gradle.kotlin.dsl.property
import java.nio.file.Files
import java.nio.file.attribute.PosixFilePermission
import javax.inject.Inject

// TODO: fix up-to-date and simplify this
open class EditFile @Inject constructor(
  objectFactory: ObjectFactory,
  projectLayout: ProjectLayout
) : DefaultTask() {

//  init {
// TODO: fix up-to-dat
//    outputs.upToDateWhen { false }
//  }

  @get:Internal
  val file: RegularFileProperty = objectFactory.fileProperty()

  @get:OutputFile
  val output: Provider<RegularFile> = file

  @get:Internal
  val editActions: ListProperty<TextEditAction> = objectFactory.listProperty<TextEditAction>().empty()

  @get:Input
  @get:Optional
  val executable: Property<Boolean> = objectFactory.property()

  @TaskAction
  fun convergeFile() {
    val targetFile = output.get().asFile
    val textToWrite = when (val transformation = performTransformation()) {
      is Either.Left -> {
        logger.debug("No transformations needed for {}", targetFile)
        transformation.value
      }
      is Either.Right -> transformation.value
    }
    targetFile.writeText(textToWrite)

    if (executable.getOrElse(false)) {
      val destinationPath = targetFile.toPath()
      val currentPermission = Files.getPosixFilePermissions(destinationPath)
      Files.setPosixFilePermissions(
        destinationPath,
        currentPermission + setOf(
          PosixFilePermission.OWNER_EXECUTE,
          PosixFilePermission.GROUP_EXECUTE
        )
      )
    }
  }

  private fun readFileTextOrDefault(): String = file.get().asFile.run {
    if (exists()) {
      readText()
    } else {
      ""
    }
  }

  private fun performTransformation(): Either<String, String> {
    val fileText = readFileTextOrDefault()
    val text: Either<String, String> = Either.Left(fileText)
    val afterApplied = editActions.get().fold(text) { acc, action ->
      when (acc) {
        is Either.Left -> action.applyTo(acc.value)
        is Either.Right -> action.applyTo(acc.value)
      }
    }

    return when (afterApplied) {
      is Either.Left -> {
        if (afterApplied.value == fileText) {
          afterApplied
        } else {
          Either.Right(afterApplied.value)
        }
      }
      is Either.Right -> {
        if (afterApplied.value == fileText) {
          Either.Left(afterApplied.value)
        } else {
          afterApplied
        }
      }
    }
  }
}
