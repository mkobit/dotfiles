  import com.squareup.kotlinpoet.TypeSpec

  fun main() {
    println(TypeSpec.enumBuilder("MyEnum")
        .addEnumConstant("thing-with-hyphen")
        .build())

    println("-".repeat(20))

    println(TypeSpec.enumBuilder("name-with-hyphen")
        .addEnumConstant("thing-with-hyphen")
        .build())

    println("-".repeat(20))

    try {
      TypeSpec.enumBuilder("continue")
          .addEnumConstant("thing-with-hyphen")
          .build()
    } catch (exception: Exception) {
      exception.printStackTrace()
    }

    println("-".repeat(20))

    try {
    println(TypeSpec.enumBuilder("MyEnum")
        .addEnumConstant("continue")
        .build())
    } catch (exception: Exception) {
      exception.printStackTrace()
    }
  }
