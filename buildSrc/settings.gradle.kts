buildCache {
  local(DirectoryBuildCache::class) {
    isEnabled = true
    setDirectory(file(".gradle-buildsrc-cache"))
  }
}
