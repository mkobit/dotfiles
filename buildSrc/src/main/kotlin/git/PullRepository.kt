package git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.file.DirectoryVar
import org.gradle.api.file.ProjectLayout
import org.gradle.api.provider.PropertyState
import org.gradle.api.tasks.InputDirectory
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

  var repositoryDirectoryProvider: Directory? = null

  @get:InputDirectory
  val repositoryDirectory: File?
    get() = repositoryDirectoryProvider?.get()

  @TaskAction
  fun pullRepository() {
    if (project.gradle.startParameter.isOffline) {
      LOGGER.warn { "Can not pull repository $repositoryDirectory when offline" }
      return
    }
    workerExecutor.submit(PullAction::class.java) {
      it.apply {
        isolationMode = IsolationMode.NONE
        setParams(repositoryDirectory!!)
      }
    }
  }
}
