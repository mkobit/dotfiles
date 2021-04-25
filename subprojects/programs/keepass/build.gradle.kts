import dotfilesbuild.utilities.home

plugins {
  id("dotfilesbuild.keepass.program")
  id("dotfilesbuild.dotfiles-lifecycle")
}

keepass {
  keepassVersion.set("2.42.1")
  secretFile.set(home.file("/home/mkobit/Programs/kobit.kdbx"))
}
