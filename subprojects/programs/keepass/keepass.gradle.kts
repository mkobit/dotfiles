import dotfilesbuild.homeFile

plugins {
  dotfilesbuild.`dotfiles-lifecycle`

  dotfilesbuild.keepass.program
}

keepass {
  keepassVersion.set("2.42.1")
  secretFile.set(homeFile("/home/mkobit/Programs/kobit.kdbx"))
}
