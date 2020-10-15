// package dotfilesbuild.io.git
//
// import com.jcraft.jsch.Session
// import org.eclipse.jgit.api.Git
// import org.eclipse.jgit.transport.JschConfigSessionFactory
// import org.eclipse.jgit.transport.OpenSshConfig
// import org.eclipse.jgit.transport.SshTransport
// import org.eclipse.jgit.transport.URIish
// import org.gradle.api.DefaultTask
// import org.gradle.api.file.DirectoryProperty
// import org.gradle.api.model.ObjectFactory
// import org.gradle.api.provider.MapProperty
// import org.gradle.api.provider.Property
// import org.gradle.api.tasks.Internal
// import org.gradle.api.tasks.TaskAction
// import org.gradle.kotlin.dsl.property
// import org.gradle.workers.WorkAction
// import org.gradle.workers.WorkParameters
// import org.gradle.workers.WorkerExecutor
// import java.nio.file.Files
// import javax.inject.Inject
//
// open class ManageGitRepository @Inject constructor(
//  private val objectFactory: ObjectFactory,
//  private val workerExecutor: WorkerExecutor
// ) : DefaultTask() {
//
//  companion object {
//    private val nonHostKeyCheckingConfigFactory = object : JschConfigSessionFactory() {
//      override fun configure(hc: OpenSshConfig.Host, session: Session) {
//        if (hc.hostName.contains("gitlab.com")) {
//          // TODO: Hack for host key checking for GitLab on laptop not doing what I expect
//          // https://stackoverflow.com/questions/13396534/unknownhostkey-exception-in-accessing-github-securely
//          session.setConfig("StrictHostKeyChecking", "no")
//        }
//      }
//    }
//  }
//
//  @get:Internal
//  val gitRepositorySpec: Property<GitVersionControlTarget> = objectFactory.property()
//
//  @TaskAction
//  fun synchronizeRepository() {
//    require(gitRepositorySpec.isPresent) { "Git repository spec must be present" }
//    val queue = workerExecutor.noIsolation()
//    queue.submit(ManageGitRepositoryWorkAction::class.java) {
//      gitDirectory.set(gitRepositorySpec.flatMap { it.directory })
//      remotes.set(gitRepositorySpec.map { it.remotes })
//    }
//  }
//
//  internal abstract class ManageGitRepositoryWorkAction : WorkAction<ManageGitRepositoryWorkParameters> {
//    override fun execute() {
//      // init/open
//      val directory = parameters.gitDirectory.get().asFile
//      val remotes = parameters.remotes.get()
//      directory.let {
//        if (!Files.isDirectory(it.toPath())) {
//          Git.init().setDirectory(it).call()
//        } else {
//          Git.open(it)
//        }
//      }.use { git ->
//        // remotes
//        val currentRemotes = git.remoteList().call()
//          .asSequence()
//          .onEach { require(it.urIs.size == 1) { "Only supports single URL from each remote" } }
//          .associate { it.name to it.urIs.first().toASCIIString() }
//        val toRemove = currentRemotes.filter { it.key !in remotes }
//        val toAdd = remotes.filter { it.key !in currentRemotes }
//        val toUpdate = remotes.filter { it.key in currentRemotes && currentRemotes[it.key] != it.value }
//
//        if (toRemove.isEmpty() && toAdd.isEmpty() && toUpdate.isEmpty()) {
// //          logger.debug("No remotes configuration needed for {}", git.repository.directory)
//        }
//
//        toRemove.forEach { (name, _) ->
// //          logger.debug("Removing remote named {} from repository {}", name, git.repository.directory)
//          git.remoteRemove().apply {
//            setName(name)
//          }.call()
//        }
//        toAdd.forEach { (name, uri) ->
// //          logger.debug("Add remote named {} with URI {} to repository {}", name, uri, git.repository.directory)
//          git.remoteAdd().setName(name)
//            .setUri(URIish(uri))
//            .call()
//        }
//        toUpdate.forEach { (name, uri) ->
// //          logger.debug("Updating remote with name {} from URI {} to URI {} in repository {}",
// //            name,
// //            currentRemotes[name],
// //            uri,
// //            git.repository.directory
// //          )
//          git.remoteSetUrl().apply {
//            setName(name)
//            setUri(URIish(uri))
//          }.call()
//        }
//
//        // fetch
//        git.fetch()
//          .setTransportConfigCallback { transport ->
//            if (transport is SshTransport) {
//              transport.sshSessionFactory = nonHostKeyCheckingConfigFactory
//            }
//          }
//          .call()
//      }
//    }
//  }
//
//  internal interface ManageGitRepositoryWorkParameters : WorkParameters {
//    val gitDirectory: DirectoryProperty
//    val remotes: MapProperty<String, String>
//  }
// }
