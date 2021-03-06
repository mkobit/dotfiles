package com.mkobit.cdp

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.squareup.kotlinpoet.ANY
import com.squareup.kotlinpoet.AnnotationSpec
import com.squareup.kotlinpoet.BOOLEAN
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.INT
import com.squareup.kotlinpoet.KModifier
import com.squareup.kotlinpoet.ParameterSpec
import com.squareup.kotlinpoet.ParameterizedTypeName.Companion.parameterizedBy
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.TypeAliasSpec
import com.squareup.kotlinpoet.TypeName
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.asClassName
import com.squareup.kotlinpoet.asTypeName
import mu.KotlinLogging
import java.nio.file.Files
import java.nio.file.Path

private val LOGGER = KotlinLogging.logger { }

data class ChromeDebugProtocolGenerationRequest(
  val basePackage: String,
  val protocolJsonFiles: List<Path>,
  val destinationBaseDirectory: Path
) {
  init {
    protocolJsonFiles.forEach {
      require(Files.isRegularFile(it))
    }
  }
}

private fun TypeAliasSpec.Builder.maybeAddKdoc(format: String?) = apply {
  if (format != null) {
    addKdoc(CodeBlock.of("%L", format))
  }
}

private fun FunSpec.Builder.maybeAddKdoc(format: String?) = apply {
  if (format != null) {
    addKdoc(CodeBlock.of("%L", format))
  }
}

private fun TypeSpec.Builder.maybeAddKdoc(format: String?) = apply {
  if (format != null) {
    addKdoc(CodeBlock.of("%L", format))
  }
}

private fun PropertySpec.Builder.maybeAddKdoc(format: String?) = apply {
  if (format != null) {
    addKdoc(CodeBlock.of("%L", format))
  }
}

private fun ChromeDebugProtocolGenerationRequest.packageNameForDomain(domain: String): String = "$basePackage.domain.${domain.toLowerCase()}"

// https://raw.githubusercontent.com/chromium/chromium/1011f64b2bab81798342a15508cb7c053e252ded/third_party/blink/renderer/core/inspector/browser_protocol-1.3.json
fun generateChromeDebugProtocol(request: ChromeDebugProtocolGenerationRequest) {
  val mapper = ObjectMapper()
  val experimentalClassName = ClassName(request.basePackage, "ExperimentalChromeApi")
  val experimentalChromeApi = TypeSpec.annotationBuilder(experimentalClassName)
    .addAnnotation(
      AnnotationSpec.builder(ClassName("kotlin", "RequiresOptIn"))
        .addMember(CodeBlock.of("level = RequiresOptIn.Level.WARNING"))
        .build()
    )
    .addKdoc("Marks an experimental Chrome API.")
    .build()
  FileSpec.get(request.basePackage, experimentalChromeApi)
    .writeTo(request.destinationBaseDirectory)
  request.protocolJsonFiles.forEach {
    val json = mapper.readTree(it.toFile())
    val version = json["version"]
    val major = version["major"]
    val minor = version["minor"]
    json["domains"]
      .map { domainNode -> generateDomain(request, domainNode, AnnotationSpec.builder(experimentalClassName).build()) }
  }
}

private fun generateDomain(request: ChromeDebugProtocolGenerationRequest, domainNode: JsonNode, experimental: AnnotationSpec) {
  val domain = domainNode["domain"].asText()
  LOGGER.debug { "Generating domain $domain" }
  domainNode["types"]?.let { typesNode ->
    generateTypes(domain, request, typesNode, experimental)
  }
  generateCommands(domainNode, request, experimental)
  // TODO: generate things for 'events'
}

private fun generateCommands(
  domainNode: JsonNode,
  request: ChromeDebugProtocolGenerationRequest,
  experimental: AnnotationSpec
) {
  val domain = domainNode["domain"].asText()
  val domainsNode = domainNode["commands"]
  val domainInterfaceTypeName = ClassName(request.packageNameForDomain(domain), "${domain.capitalize()}Domain")
  val domainInterfaceTypeSpecBuilder = TypeSpec.interfaceBuilder(domainInterfaceTypeName).apply {
    val description = domainNode["description"]?.asText()
    if (domainNode["experimental"]?.asBoolean() == true) {
      addAnnotation(experimental)
    }
    if (domainNode["deprecated"]?.asBoolean() == true) {
      val deprecatedSpec = AnnotationSpec.builder(Deprecated::class)
        .addMember("message = %S", "deprecated in protocol definition")
        .build()
      addAnnotation(deprecatedSpec)
    }
    maybeAddKdoc(description)
  }
  domainsNode.forEach { commandNode ->
    val commandName = commandNode["name"].asText()
    val commandDescription = commandNode["description"]?.asText()
    val commandParameters: JsonNode? = commandNode["parameters"]
    val commandReturns: JsonNode? = commandNode["returns"]
    val commandFunSpecBuilder = FunSpec.builder(commandName)
      .maybeAddKdoc(commandDescription)
      .addModifiers(KModifier.SUSPEND, KModifier.ABSTRACT)

    val commandRequestResponseFileSpec = FileSpec.builder(request.packageNameForDomain(domain), "${commandName}Command")

    if (commandParameters != null) {
      val commandRequestTypeName = ClassName(request.packageNameForDomain(domain), "${commandName.capitalize()}Request")
      commandFunSpecBuilder.addParameter(ParameterSpec.builder("request", commandRequestTypeName).build())
      val commandParameterRequestTypeSpecBuilder = TypeSpec.classBuilder(commandRequestTypeName)
        .addModifiers(KModifier.DATA)
      val commandParameterRequestConstructorBuilder = FunSpec.constructorBuilder()
      commandParameters.forEach { commandParameter ->
        val parameterName = commandParameter["name"].asText()
        val parameterDescription = commandParameter["description"]?.asText()
        val parameterTypeName = determineTypeForNode(domain, request, commandParameter)
        val commandRequestProperty = PropertySpec.builder(parameterName, parameterTypeName)
          .initializer(parameterName)
          .maybeAddKdoc(parameterDescription)
          .build()
        val commandRequestParameter = ParameterSpec.builder(parameterName, parameterTypeName)
          .build()

        commandParameterRequestTypeSpecBuilder.addProperty(commandRequestProperty)
        commandParameterRequestConstructorBuilder.addParameter(commandRequestParameter)
      }
      commandRequestResponseFileSpec.addType(
        commandParameterRequestTypeSpecBuilder
          .primaryConstructor(commandParameterRequestConstructorBuilder.build())
          .build()
      )
    }

    if (commandReturns != null) {
      val commandReplyTypeName = ClassName(request.packageNameForDomain(domain), "${commandName.capitalize()}Reply")
      commandFunSpecBuilder.returns(commandReplyTypeName)
      val commandParameterReplyTypeSpecBuilder = TypeSpec.classBuilder(commandReplyTypeName)
        .addModifiers(KModifier.DATA)
      val commandParameterReplyConstructorBuilder = FunSpec.constructorBuilder()
      commandReturns.forEach { commandReturn ->
        val returnName = commandReturn["name"].asText()
        val returnTypeName = determineTypeForNode(domain, request, commandReturn)
        val returnDescription = commandReturn["description"]?.asText()
        val returnProperty = PropertySpec.builder(returnName, returnTypeName)
          .initializer(returnName)
          .maybeAddKdoc(returnDescription)
          .build()
        val returnParameter = ParameterSpec.builder(returnName, returnTypeName)
          .build()
        commandParameterReplyTypeSpecBuilder.addProperty(returnProperty)
        commandParameterReplyConstructorBuilder.addParameter(returnParameter)
      }
      commandRequestResponseFileSpec.addType(
        commandParameterReplyTypeSpecBuilder
          .primaryConstructor(commandParameterReplyConstructorBuilder.build())
          .build()
      )
    }
    commandRequestResponseFileSpec.build().let {
      if (it.members.isNotEmpty()) {
        it.writeTo(request.destinationBaseDirectory)
      }
    }

    domainInterfaceTypeSpecBuilder.addFunction(commandFunSpecBuilder.build())
  }
  val domainInterfaceTypeSpec = domainInterfaceTypeSpecBuilder.build()
  val domainFile = FileSpec.get(request.packageNameForDomain(domain), domainInterfaceTypeSpec)
  domainFile.writeTo(request.destinationBaseDirectory)
}

private fun generateTypes(
  domain: String,
  request: ChromeDebugProtocolGenerationRequest,
  typesNode: JsonNode,
  experimental: AnnotationSpec
) {
  val fileSpecBuilder = FileSpec.builder(request.packageNameForDomain(domain), "types")

  typesNode.forEach { typeNode ->
    val typeName = typeNode["id"].asText()
    val typeDescription = typeNode["description"]?.asText()
    when (val type = typeNode["type"].asText()) {
      "string" -> {
        val enum = typeNode["enum"]?.map { it.asText() }
        if (enum != null) {
          fun nameToEnumValue(value: String) = value.toUpperCase().replace("-", "_")

          val enumBuilder = TypeSpec.enumBuilder(typeName)
            .maybeAddKdoc(typeDescription)
          enum
            .forEach {
              val jsonProperty = AnnotationSpec.builder(JsonProperty::class.asClassName())
                .addMember(CodeBlock.of("value = %S", it))
                .build()
              enumBuilder.addEnumConstant(nameToEnumValue(it), TypeSpec.anonymousClassBuilder().addAnnotation(jsonProperty).build())
            }
          fileSpecBuilder.addType(enumBuilder.build())
        } else {
          val stringTypeAlias = TypeAliasSpec
            .builder(typeName, String::class.asTypeName())
            .apply {
              if (typeDescription != null) {
                addKdoc(CodeBlock.of("%L", typeDescription))
              }
            }
            .build()
          fileSpecBuilder.addTypeAlias(stringTypeAlias)
        }
      }
      "number" -> {
        val numberTypeAlias = TypeAliasSpec.builder(typeName, Number::class.asTypeName())
          .maybeAddKdoc(typeDescription)
          .build()
        fileSpecBuilder.addTypeAlias(numberTypeAlias)
      }
      "integer" -> {
        val integerTypeAlias = TypeAliasSpec.builder(typeName, Int::class.asTypeName())
          .maybeAddKdoc(typeDescription)
          .build()
        fileSpecBuilder.addTypeAlias(integerTypeAlias)
      }
      "object" -> {
        val propertiesNode: JsonNode? = typeNode["properties"]
        when {
          propertiesNode != null -> {
            val objectTypeSpecBuilder = TypeSpec.classBuilder(typeName)
              .addModifiers(KModifier.DATA)
              .maybeAddKdoc(typeDescription)
            val constructorSpecBuilder = FunSpec.constructorBuilder()
            propertiesNode.forEach { propertyNode ->
              val propertyDescription = propertyNode["description"]?.asText()
              val propertyName = propertyNode["name"].asText()
              val propertyTypeName: TypeName = determineTypeForNode(domain, request, propertyNode)
              // TODO: issues with keyword named variables at https://github.com/square/kotlinpoet/issues/483
              val propertySpec = PropertySpec.builder(propertyName, propertyTypeName)
                .initializer(propertyName)
                .maybeAddKdoc(propertyDescription)
                .build()
              val parameterSpec = ParameterSpec.builder(propertyName, propertyTypeName).build()
              constructorSpecBuilder.addParameter(parameterSpec)
              objectTypeSpecBuilder.addProperty(propertySpec)
            }
            val objectTypeSpec = objectTypeSpecBuilder.primaryConstructor(constructorSpecBuilder.build()).build()
            fileSpecBuilder.addType(objectTypeSpec)
          }
          typeName in setOf("Headers", "MemoryDumpConfig") -> {
            // special case some special 'object' types
            val mapTypeName = ClassName("kotlin.collections", "Map")
              .parameterizedBy(String::class.asTypeName(), ANY)
            val mapTypeAliasSpec = TypeAliasSpec.builder(typeName, mapTypeName)
              .maybeAddKdoc(typeDescription)
              .build()
            fileSpecBuilder.addTypeAlias(mapTypeAliasSpec)
          }
          else -> throw IllegalArgumentException("unknown/unsupported type $typeNode")
        }
      }
      "array" -> {
        val arrayItemsTypeName: TypeName = determineTypeForNode(domain, request, typeNode["items"])
        val arrayTypeName = ClassName("kotlin.collections", "List")
          .parameterizedBy(arrayItemsTypeName)
        val arrayTypeAliasSpec = TypeAliasSpec.builder(typeName, arrayTypeName)
          .maybeAddKdoc(typeDescription)
          .build()
        fileSpecBuilder.addTypeAlias(arrayTypeAliasSpec)
      }
      else -> TODO("unsupported type $type -> $typeNode")
    }
  }

  val fileSpec = fileSpecBuilder.build()
  fileSpec.writeTo(request.destinationBaseDirectory)
}

private fun determineTypeForNode(
  domain: String,
  request: ChromeDebugProtocolGenerationRequest,
  node: JsonNode
): TypeName {
  val propertyType: String? = node["type"]?.asText()
  val propertyRef: String? = node["\$ref"]?.asText()
  val isPropertyOptional = node["optional"]?.asBoolean() ?: false

  return when {
    propertyType != null -> {
      // actual type is specified
      when (propertyType) {
        "string" -> String::class.asTypeName().copy(nullable = isPropertyOptional)
        "integer" -> INT.copy(nullable = isPropertyOptional)
        "number" -> Number::class.asTypeName().copy(nullable = isPropertyOptional)
        "boolean" -> BOOLEAN.copy(nullable = isPropertyOptional)
        "array" -> {
          val arrayItemsType = determineTypeForNode(domain, request, node["items"])
          ClassName("kotlin.collections", "List")
            .parameterizedBy(arrayItemsType)
        }
        "object" -> {
          // special case for some things
          val propertyName: String? = node["name"]?.asText()
          if (propertyName == null) {
            ClassName("kotlin.collections", "List")
              .parameterizedBy(ANY)
          } else if (propertyName in setOf("highlight")) {
            ANY
          } else {
            require(
              propertyName in
                setOf(
                  "executionContextAuxData",
                  "auxData",
                  "auxAttributes",
                  "featureStatus"
                )
            ) {
              "Unsupported property type '$propertyType' for node $node"
            }
            ClassName("kotlin.collections", "Map")
              .parameterizedBy(String::class.asTypeName(), ANY)
          }
        }
        "any" -> ANY.copy(nullable = isPropertyOptional)
        else -> throw java.lang.IllegalArgumentException("Unable to handle property type $propertyType for $node")
      }
    }
    propertyRef != null -> {
      if ("." in propertyRef) {
        // located in different domain
        val (propertyRefDomain, propertyRefTypeName) = propertyRef.split(".")
        ClassName(request.packageNameForDomain(propertyRefDomain), propertyRefTypeName).copy(nullable = isPropertyOptional)
      } else {
        // located in same domain
        ClassName(request.packageNameForDomain(domain), propertyRef).copy(nullable = isPropertyOptional)
      }
    }
    else -> throw IllegalArgumentException("Unknown how to determine type for domain $domain node $node")
  }
}
