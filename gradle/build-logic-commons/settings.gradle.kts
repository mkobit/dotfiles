rootProject.name = "build-logic-commons"

apply(from = file("../shared.settings.gradle.kts"))

include("basics")
include("version-catalog")
