package dotfilesbuild.io.git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.submit
import org.gradle.workers.IsolationMode
import org.gradle.workers.WorkerExecutor
import javax.inject.Inject

@Deprecated("Simplification in-progress")
open class FetchRemotes @Inject constructor(
  private val workerExecutor: WorkerExecutor
) : DefaultTask() {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  @get:Internal
  val repositoryDirectory: DirectoryProperty = project.objects.directoryProperty()

  @TaskAction
  fun fetchRemotes() {
    workerExecutor.submit(FetchAction::class) {
      isolationMode = IsolationMode.NONE
      setParams(repositoryDirectory.get().asFile)
    }
  }
}
