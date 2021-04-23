import dotfilesbuild.home

plugins {
  id("dotfilesbuild.keepass.program")
}

keepass {
  keepassVersion.set("2.42.1")
  secretFile.set(home.file("/home/mkobit/Programs/kobit.kdbx"))
}
