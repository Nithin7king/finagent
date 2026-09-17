package ai.myfy.gateway

import ai.myfy.gateway.config.DatabaseConfig
import ai.myfy.gateway.config.EnvConfig
import ai.myfy.gateway.proxy.reverseProxyRoutes
import ai.myfy.gateway.routes.authRoutes
import ai.myfy.gateway.routes.notificationRoutes
import com.fasterxml.jackson.databind.SerializationFeature
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpMethod
import io.ktor.serialization.jackson.jackson
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.plugins.cors.routing.CORS
import io.ktor.server.routing.routing
import org.slf4j.LoggerFactory

private val logger = LoggerFactory.getLogger("FinAgentGateway")

fun main() {
    val port = EnvConfig.port
    val fastApiUrl = EnvConfig.fastApiUrl

    println("==================================================")
    println("🚀 [FinAgent Kotlin Gateway]")
    println("Running on:          http://localhost:$port")
    println("FastAPI Backend:     $fastApiUrl")
    println("Database:            ${EnvConfig.databaseUrl.substringBefore('@')}@...")
    println("==================================================")

    val server = embeddedServer(Netty, port = port, host = "0.0.0.0", module = Application::module)

    Runtime.getRuntime().addShutdownHook(Thread {
        println("[FinAgent Kotlin Gateway] Shutting down...")
        DatabaseConfig.close()
        server.stop(1000, 2000)
    })

    server.start(wait = true)
}

fun Application.module() {
    install(CORS) {
        allowHost("localhost:8501", schemes = listOf("http", "https"))
        allowHost("127.0.0.1:8501", schemes = listOf("http", "https"))
        allowHost("localhost:3000", schemes = listOf("http", "https"))
        allowHost("localhost:8080", schemes = listOf("http", "https"))
        anyHost() // For mobile/emulator connections

        allowHeader(HttpHeaders.ContentType)
        allowHeader(HttpHeaders.Authorization)
        allowHeader("X-Requested-With")
        allowHeader("x-user-id")

        allowMethod(HttpMethod.Options)
        allowMethod(HttpMethod.Get)
        allowMethod(HttpMethod.Post)
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowMethod(HttpMethod.Patch)

        allowCredentials = true
    }

    install(ContentNegotiation) {
        jackson {
            enable(SerializationFeature.INDENT_OUTPUT)
        }
    }

    routing {
        // 1. Native Kotlin Authentication Routes (/api/auth/register, /api/auth/login)
        authRoutes()

        // 2. Notification delivery webhook (/notifications/deliver)
        notificationRoutes()

        // 3. Reverse Proxy Route (/api/*) -> FastAPI backend with x-user-id injection
        reverseProxyRoutes()
    }
}
