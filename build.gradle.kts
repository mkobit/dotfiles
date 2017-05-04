import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import org.gradle.api.tasks.wrapper.Wrapper
import java.nio.file.Files

description = "Dotfiles and package management of laptop"

open class Symlink : DefaultTask() {

  /**
   * The source file of the link.
   */
  @get:InputFile
  var source: File? = null

  /**
   * The destination where the link will be created.
   */
  @get:OutputFile
  var destination: File? = null

  @TaskAction
  fun createLink() {
    val sourcePath = source!!.toPath().toAbsolutePath()
    val destinationPath = destination!!.toPath().toAbsolutePath()
    if (Files.isSymbolicLink(destinationPath)) {
      logger.info("{} is an existing symbolic link, delete before recreating", destinationPath)
      Files.delete(destinationPath)
    } else if (Files.exists(destinationPath)) {
      throw InvalidUserDataException("$destinationPath already exists, and isn't a symlink.")
    } else {
      logger.debug("Creating symbolic link at {} for {}", destinationPath, sourcePath)
      Files.createSymbolicLink(destinationPath, sourcePath)
    }
  }
}

val homeDir = file(System.getProperty("user.home"))

fun homeFile(filename: Any): File = project.file("$homeDir/$filename")

fun projectFile(relativePath: Any): File = project.file("$rootDir/$relativePath")

tasks {
  val synchronize by creating(Exec::class) {
    commandLine("git", "pull", "--rebase", "--autostash")
  }
  val gitIgnoreGlobal by creating(Symlink::class) {
    source = projectFile("git/gitignore_global.dotfile")
    destination = homeFile(".gitignore_global")
  }
  val git by creating {
    group = "Git"
    dependsOn(gitIgnoreGlobal)
  }

  val screenRc by creating(Symlink::class) {
    source = projectFile("screen/screenrc.dotfile")
    destination = homeFile(".screenrc")
  }

  val screen by creating {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by creating(Symlink::class) {
    source = projectFile("tmux/tmux.conf.dotfile")
    destination = homeFile(".tmux.conf")
  }

  val tmux by creating {
    group = "Tmux"
    dependsOn(tmuxConf)
  }

  val vimRc by creating(Symlink::class) {
    source = projectFile("vim/vimrc.dotfile")
    destination = homeFile(".vimrc")
  }

  val vim by creating {
    group = "VIM"
    dependsOn(vimRc)
  }

  "dotfiles" {
    description = "Sets up all dotfiles and packages"
    group = "Install"
    dependsOn(git, screen, tmux, vim)
  }

  "wrapper"(Wrapper::class) {
    gradleVersion = "3.5"
  }

  project.defaultTasks(synchronize.name)
}
