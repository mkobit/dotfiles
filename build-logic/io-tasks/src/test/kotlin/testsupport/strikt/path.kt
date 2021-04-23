package testsupport.strikt

import strikt.api.Assertion
import java.nio.file.Files
import java.nio.file.Path

val <T : Path> Assertion.Builder<T>.content: Assertion.Builder<String>
  get() = get("file dotfilesbuild.io.file.content") { Files.readAllBytes(this).toString(Charsets.UTF_8) }
