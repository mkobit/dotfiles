package dotfilesbuild.legacy.file

import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.file.FileType
import org.gradle.api.model.ObjectFactory
import org.gradle.api.tasks.InputFiles
import org.gradle.api.tasks.OutputDirectory
import org.gradle.api.tasks.PathSensitive
import org.gradle.api.tasks.PathSensitivity
import org.gradle.api.tasks.TaskAction
import org.gradle.work.ChangeType
import org.gradle.work.Incremental
import org.gradle.work.InputChanges
import org.gradle.workers.WorkerExecutor
import java.nio.file.Files
import javax.inject.Inject

open class CalculateChecksum @Inject constructor(
  objectFactory: ObjectFactory,
  private val workerExecutor: WorkerExecutor
) : DefaultTask() {

  @get:Incremental
  @get:InputFiles
  @get:PathSensitive(PathSensitivity.RELATIVE)
  val digestFiles = objectFactory.fileCollection()

  @get:OutputDirectory
  val checksums: DirectoryProperty = objectFactory.directoryProperty()

  @TaskAction
  fun compute(inputChanges: InputChanges) {
    if (!inputChanges.isIncremental) {
      checksums.get().asFile.deleteRecursively()
    }

    val queue = workerExecutor.noIsolation()

    inputChanges.getFileChanges(digestFiles)
      .filter { change -> change.fileType != FileType.DIRECTORY }
      .forEach { change ->
        when (change.changeType) {
          ChangeType.ADDED -> queue.submit(HashWorkAction::class.java) {
            source.set(change.file)
            destination.set(checksums.file("${change.normalizedPath}.sha256"))
            algorithm.set("SHA-256")
          }
          ChangeType.MODIFIED -> queue.submit(HashWorkAction::class.java) {
            source.set(change.file)
            destination.set(checksums.file("${change.normalizedPath}.sha256"))
            algorithm.set("SHA-256")
          }
          ChangeType.REMOVED -> {
            Files.delete(checksums.file("${change.normalizedPath}.sha256").get().asFile.toPath())
          }
        }
      }
  }
}
