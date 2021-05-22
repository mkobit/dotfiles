plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

val vimPluginsDir = layout.buildDirectory.dir("vim-plugin-downloads")

repositories {
  exclusiveContent {
    forRepository {
      ivy {
        name = "github"
        url = uri("https://github.com")
        patternLayout {
          artifact("/[organisation]/[module]/archive/[revision].[ext]")
        }
        metadataSources { artifact() }
      }
    }
    filter {
      includeGroup("junegunn")
    }
  }
}

val vimPlugins by configurations.creating

dependencies {
  vimPlugins("junegunn:vim-plug:master@zip") {
    isChanging = true
  }
}


tasks {
  val resolveVimPlugins by registering(Sync::class) {
    from(vimPlugins)
    into(vimPluginsDir)
  }

  val stageVimFiles by registering(Sync::class) {
    from(layout.projectDirectory.dir("config"))
    into(layout.buildDirectory.dir("generated-vim-config-staging"))
  }

  val syncStaged by registering(Sync::class) {
    from(stageVimFiles)
    into(layout.buildDirectory.dir("generated-vim-config"))
  }

  dotfiles {
    // add directive to ~/.vimrc to vim file
    // :source <path>
    dependsOn(syncStaged)
  }
}
