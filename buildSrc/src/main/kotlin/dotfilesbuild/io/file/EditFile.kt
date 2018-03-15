package dotfilesbuild.io.file

import arrow.core.Either
import arrow.effects.IO
import dotfilesbuild.io.file.content.TextEditAction
import listProperty
import org.gradle.api.DefaultTask
import org.gradle.api.file.ProjectLayout
import org.gradle.api.file.RegularFile
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.ListProperty
import org.gradle.api.provider.Provider
import org.gradle.api.provider.ProviderFactory
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import javax.inject.Inject

open class EditFile @Inject constructor(
    objectFactory: ObjectFactory,
    providerFactory: ProviderFactory,
    projectLayout: ProjectLayout
) : DefaultTask() {

  init {
    outputs.upToDateWhen {
      performTransformation().isLeft()
    }
  }

  @get:InputFile
  val file: RegularFileProperty = projectLayout.fileProperty()

  @get:OutputFile
  val output: Provider<RegularFile> = file

  @get:Internal
  val editActions: ListProperty<TextEditAction> = objectFactory.listProperty()

  @TaskAction
  fun convergeFile() {
    val targetFile = output.get().asFile
    val transformation = performTransformation()
    when(transformation) {
      is Either.Left -> logger.debug("No transformations needed for {}", targetFile)
      is Either.Right -> targetFile.writeText(transformation.b)
    }
  }

  private fun readFileText(): String = file.get().asFile.readText()

  private fun performTransformation(): Either<String, String> {
    require(editActions.get().isNotEmpty()) { "EditActions cannot be empty" }
    val fileIo = IO { readFileText() }
    val firstAction = editActions.get().first()
    val fileText = readFileText()
    val text: Either<String, String> = Either.left(fileText)
    val afterApplied = editActions.get().fold(text) { acc, action ->
      when(acc) {
        is Either.Left -> action.applyTo(acc.a)
        is Either.Right -> action.applyTo(acc.b)
      }
    }

    return when(afterApplied) {
      is Either.Left -> {
        if (afterApplied.a == fileText) {
          afterApplied
        } else {
          Either.right(afterApplied.a)
        }
      }
      is Either.Right -> {
        if (afterApplied.b == fileText) {
          Either.left(afterApplied.b)
        } else {
          afterApplied
        }
      }
    }
  }
//
//  private fun Collection<TextEditAction>.applyAll() {
//    val initialText = readFileText()
//    val initialState = State<String, Option<String>> { initialText toT None }
//    val nelActions = Nel.fromListUnsafe(editActions.get())
//    nelActions
//    State().monad<String>().binding {
//      val a = this@applyAll.first().execute().bind()
//
//      yields()
//    }
//    this.fold(initialState) { accumulator, action ->
//      accumulator.ap()
//    }
// }
}

