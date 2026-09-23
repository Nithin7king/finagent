package ai.myfy.gateway.proxy

import ai.myfy.gateway.auth.JwtService
import ai.myfy.gateway.config.EnvConfig
import ai.myfy.gateway.models.ErrorResponse
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.cio.CIO
import io.ktor.client.request.headers
import io.ktor.client.request.request
import io.ktor.client.request.setBody
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpMethod
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.ApplicationCall
import io.ktor.server.application.call
import io.ktor.server.request.header
import io.ktor.server.request.httpMethod
import io.ktor.server.request.receiveChannel
import io.ktor.server.request.uri
import io.ktor.server.response.header
import io.ktor.server.response.respond
import io.ktor.server.response.respondBytes
import io.ktor.server.routing.Route
import io.ktor.server.routing.route
import io.ktor.utils.io.ByteReadChannel
import org.slf4j.LoggerFactory

private val logger = LoggerFactory.getLogger("ReverseProxy")

object ProxyClient {
    val client = HttpClient(CIO) {
        engine {
            requestTimeout = 60000
        }
    }
}

fun Route.reverseProxyRoutes() {
    // Catch-all route for /api/*
    route("/api/{path...}") {
        handle {
            handleProxy(call)
        }
    }

    // Direct proxy for /health if called directly on gateway
    route("/health") {
        handle {
            handleProxy(call, targetPrefix = "/health")
        }
    }
}

private suspend fun handleProxy(call: ApplicationCall, targetPrefix: String? = null) {
    val requestUri = call.request.uri
    val targetPath = targetPrefix ?: if (requestUri.startsWith("/api/")) {
        requestUri.substring(4) // keeps leading slash: "/transactions?..."
    } else {
        requestUri
    }

    val pathOnly = targetPath.substringBefore('?')
    val publicPaths = listOf(
        "/auth/login",
        "/auth/register",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    )

    if (call.request.httpMethod == HttpMethod.Options || publicPaths.any { pathOnly.startsWith(it) }) {
        forwardToFastApi(call, targetPath, userId = null)
        return
    }

    // Authenticated path — validate JWT
    val authHeader = call.request.header(HttpHeaders.Authorization)
    if (authHeader == null || !authHeader.startsWith("Bearer ")) {
        call.respond(
            HttpStatusCode.Unauthorized,
            ErrorResponse("Missing or invalid authentication credentials.")
        )
        return
    }

    val token = authHeader.removePrefix("Bearer ").trim()
    val decoded = JwtService.verifyToken(token)
    if (decoded == null) {
        call.respond(
            HttpStatusCode.Unauthorized,
            ErrorResponse("Invalid or expired authentication token.")
        )
        return
    }

    val userId = decoded.subject
    forwardToFastApi(call, targetPath, userId)
}

private suspend fun forwardToFastApi(call: ApplicationCall, targetPathWithQuery: String, userId: String?) {
    val targetUrl = "${EnvConfig.fastApiUrl}$targetPathWithQuery"
    val method = call.request.httpMethod

    try {
        val proxyResponse = ProxyClient.client.request(targetUrl) {
            this.method = method

            // Forward request headers
            call.request.headers.forEach { name, values ->
                if (!name.equals(HttpHeaders.Host, ignoreCase = true) &&
                    !name.equals(HttpHeaders.ContentLength, ignoreCase = true)
                ) {
                    values.forEach { v ->
                        this.headers.append(name, v)
                    }
                }
            }

            // Injected user ID
            if (userId != null) {
                this.headers.append("x-user-id", userId)
            }

            // Forward request body if applicable
            if (method in listOf(HttpMethod.Post, HttpMethod.Put, HttpMethod.Patch)) {
                val channel: ByteReadChannel = call.receiveChannel()
                setBody(channel)
            }
        }

        // Copy response headers
        proxyResponse.headers.forEach { name, values ->
            if (!name.equals(HttpHeaders.TransferEncoding, ignoreCase = true) &&
                !name.equals(HttpHeaders.ContentLength, ignoreCase = true)
            ) {
                values.forEach { v ->
                    call.response.header(name, v)
                }
            }
        }

        val status = HttpStatusCode.fromValue(proxyResponse.status.value)
        val bytes = proxyResponse.body<ByteArray>()

        call.respondBytes(bytes, status = status)
    } catch (e: Exception) {
        logger.error("Proxy error forwarding to $targetUrl: ${e.message}", e)
        call.respond(
            HttpStatusCode.BadGateway,
            ErrorResponse("Gateway proxy error: Unable to connect to backend service. (${e.message})")
        )
    }
}
