package dotfiles.mkobit.picocli

import picocli.CommandLine
import java.time.Instant

class RuntimeInstantIDefaultValueProvider : CommandLine.IDefaultValueProvider {
  override fun defaultValue(argSpec: CommandLine.Model.ArgSpec): String {
    return argSpec.defaultValue() ?: Instant.now().toString()
  }
}

class InstantIValueConverter : CommandLine.ITypeConverter<Instant> {
  override fun convert(value: String): Instant = Instant.parse(value)
}
