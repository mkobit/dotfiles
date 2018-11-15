package testsupport.strikt

import strikt.api.Assertion
import java.nio.file.Files
import java.nio.file.Path

fun <T : Path> Assertion.Builder<T>.exists() =
    assert("exists") {
      if (Files.exists(it)) {
        pass()
      } else {
        fail("does not exist")
      }
    }

fun <T : Path> Assertion.Builder<T>.isRegularFile() =
    assert("is regular file") {
      if (Files.isRegularFile(it)) {
        pass()
      } else {
        fail("is not regular file")
      }
    }

fun <T : Path> Assertion.Builder<T>.isDirectory() =
    assert("is directory") {
      if (Files.isDirectory(it)) {
        pass()
      } else {
        fail("is not directory")
      }
    }

val <T : Path> Assertion.Builder<T>.content: Assertion.Builder<String>
  get() = get("file content") { Files.readAllLines(this).joinToString(System.lineSeparator()) }

fun <T : Path> Assertion.Builder<T>.resolvePath(path: Path): Assertion.Builder<Path> =
    get { resolve(path) }

fun <T : Path> Assertion.Builder<T>.resolvePath(path: String): Assertion.Builder<Path> =
    get { resolve(path) }
