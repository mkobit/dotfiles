plugins {
  id("org.jlleitschuh.gradle.ktlint")
}

// issues
// 1. https://github.com/JLLeitschuh/ktlint-gradle/issues/443 - doesn't work on non-kotlin projects

ktlint {
  // https://github.com/JLLeitschuh/ktlint-gradle/issues/458: cannot use ktlint 0.41.0
  // version.set("0.41.0")
}
