plugins {
  id("dotfilesbuild.kubernetes.kubectl.program")
}

kubectl {
  version.set("v1.15.2")
}
