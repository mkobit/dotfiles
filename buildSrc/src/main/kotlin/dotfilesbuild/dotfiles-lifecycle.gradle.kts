package dotfilesbuild

plugins {
  base
}

tasks.register("dotfiles") {
  description = "Sets up all dotfiles and packages"
  group = "Install"
}
