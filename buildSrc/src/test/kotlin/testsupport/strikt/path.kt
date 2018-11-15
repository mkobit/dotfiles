package testsupport.strikt

import strikt.api.Assertion
import java.nio.file.Files
import java.nio.file.Path

fun Assertion.Builder<out Path>.exists() =
    assert("exists") {
      if (Files.exists(it)) {
        pass()
      } else {
        fail("does not exist")
      }
    }

fun Assertion.Builder<out Path>.isRegularFile() =
    assert("is regular file") {
      if (Files.isRegularFile(it)) {
        pass()
      } else {
        fail("is not regular file")
      }
    }

fun Assertion.Builder<out Path>.isDirectory() =
    assert("is directory") {
      if (Files.isDirectory(it)) {
        pass()
      } else {
        fail("is not directory")
      }
    }

val Assertion.Builder<out Path>.content: Assertion.Builder<String>
  get() = get("file content") { Files.readAllLines(this).joinToString(System.lineSeparator()) }

fun Assertion.Builder<out Path>.resolvePath(path: Path): Assertion.Builder<Path> =
    get { resolve(path) }

fun Assertion.Builder<out Path>.resolvePath(path: String): Assertion.Builder<Path> =
    get { resolve(path) }
