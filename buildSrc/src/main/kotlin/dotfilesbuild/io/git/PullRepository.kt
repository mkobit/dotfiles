package dotfilesbuild.io.git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.tasks.InputDirectory
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.workers.IsolationMode
import org.gradle.workers.WorkerExecutor
import java.io.File
import javax.inject.Inject

open class PullRepository @Inject constructor(
    private val workerExecutor: WorkerExecutor
) : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  @get:Internal
  val repositoryDirectory: DirectoryProperty = newInputDirectory()

  @TaskAction
  fun pullRepository() {
    if (project.gradle.startParameter.isOffline) {
      LOGGER.warn { "Can not pull repository $repositoryDirectory when offline" }
      return
    }
    workerExecutor.submit(PullAction::class.java) {
      isolationMode = IsolationMode.NONE
      setParams(repositoryDirectory.asFile.get(), "origin")
    }
  }
}