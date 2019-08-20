package testsupport.container

import org.testcontainers.containers.GenericContainer
import org.testcontainers.containers.wait.Wait

class ChromeContainer : GenericContainer<ChromeContainer>("chromedp/headless-shell@sha256:98fe370a2fbd3ff43bfedef0ff33a2865d11a5fba3a3cb75f88a65bb22f7f14c") {
  init {
    withExposedPorts(9222)
    waitingFor(Wait.forHttp("/json"))
  }

  val debugProtocolPort: Int get() = getMappedPort(9222)
}
