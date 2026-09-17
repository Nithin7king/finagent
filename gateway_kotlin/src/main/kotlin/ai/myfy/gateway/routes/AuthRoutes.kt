package ai.myfy.gateway.routes

import ai.myfy.gateway.auth.JwtService
import ai.myfy.gateway.auth.PasswordService
import ai.myfy.gateway.config.DatabaseConfig
import ai.myfy.gateway.models.AuthResponse
import ai.myfy.gateway.models.ErrorResponse
import ai.myfy.gateway.models.LoginRequest
import ai.myfy.gateway.models.RegisterRequest
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import org.slf4j.LoggerFactory
import java.sql.Statement
import java.sql.Timestamp
import java.time.Instant

private val logger = LoggerFactory.getLogger("AuthRoutes")

fun Route.authRoutes() {
    route("/api/auth") {
        post("/register") {
            val req = try {
                call.receive<RegisterRequest>()
            } catch (e: Exception) {
                call.respond(HttpStatusCode.BadRequest, ErrorResponse("Invalid request payload."))
                return@post
            }

            val email = req.email?.trim()?.lowercase()
            val name = req.name?.trim()
            val password = req.password

            if (email.isNullOrEmpty() || name.isNullOrEmpty() || password.isNullOrEmpty()) {
                call.respond(HttpStatusCode.BadRequest, ErrorResponse("Email, name, and password are required."))
                return@post
            }

            try {
                DatabaseConfig.getConnection().use { conn ->
                    val checkStmt = conn.prepareStatement("SELECT id FROM users WHERE email = ?")
                    checkStmt.setString(1, email)
                    val rs = checkStmt.executeQuery()
                    if (rs.next()) {
                        call.respond(HttpStatusCode.BadRequest, ErrorResponse("Email already registered."))
                        return@post
                    }

                    val hashedPassword = PasswordService.hashPassword(password)
                    val insertStmt = conn.prepareStatement(
                        """
                        INSERT INTO users (email, name, hashed_password, monthly_income, currency, created_at, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """.trimIndent(),
                        Statement.RETURN_GENERATED_KEYS
                    )
                    insertStmt.setString(1, email)
                    insertStmt.setString(2, name)
                    insertStmt.setString(3, hashedPassword)
                    insertStmt.setDouble(4, req.monthlyIncome ?: 0.0)
                    insertStmt.setString(5, req.currency ?: "INR")
                    insertStmt.setTimestamp(6, Timestamp.from(Instant.now()))
                    insertStmt.setBoolean(7, true)
                    insertStmt.executeUpdate()

                    val keys = insertStmt.generatedKeys
                    val userId = if (keys.next()) {
                        keys.getLong(1)
                    } else {
                        val getStmt = conn.prepareStatement("SELECT id FROM users WHERE email = ?")
                        getStmt.setString(1, email)
                        val grs = getStmt.executeQuery()
                        if (grs.next()) grs.getLong("id") else 1L
                    }

                    val token = JwtService.createToken(userId, email)
                    call.respond(
                        HttpStatusCode.OK,
                        AuthResponse(
                            accessToken = token,
                            userId = userId,
                            name = name,
                            email = email
                        )
                    )
                }
            } catch (e: Exception) {
                logger.error("Registration database error", e)
                call.respond(HttpStatusCode.InternalServerError, ErrorResponse("Server registration error: ${e.message}"))
            }
        }

        post("/login") {
            val req = try {
                call.receive<LoginRequest>()
            } catch (e: Exception) {
                call.respond(HttpStatusCode.BadRequest, ErrorResponse("Invalid request payload."))
                return@post
            }

            val email = req.email?.trim()?.lowercase()
            val password = req.password

            if (email.isNullOrEmpty() || password.isNullOrEmpty()) {
                call.respond(HttpStatusCode.BadRequest, ErrorResponse("Email and password are required."))
                return@post
            }

            try {
                DatabaseConfig.getConnection().use { conn ->
                    val stmt = conn.prepareStatement("SELECT id, name, email, hashed_password, is_active FROM users WHERE email = ?")
                    stmt.setString(1, email)
                    val rs = stmt.executeQuery()

                    if (!rs.next()) {
                        call.respond(HttpStatusCode.Unauthorized, ErrorResponse("Invalid email or password."))
                        return@post
                    }

                    val userId = rs.getLong("id")
                    val userName = rs.getString("name")
                    val userEmail = rs.getString("email")
                    val hashedPassword = rs.getString("hashed_password")
                    val isActive = rs.getBoolean("is_active")

                    if (!isActive || !PasswordService.verifyPassword(password, hashedPassword)) {
                        call.respond(HttpStatusCode.Unauthorized, ErrorResponse("Invalid email or password."))
                        return@post
                    }

                    val token = JwtService.createToken(userId, userEmail)
                    call.respond(
                        HttpStatusCode.OK,
                        AuthResponse(
                            accessToken = token,
                            userId = userId,
                            name = userName,
                            email = userEmail
                        )
                    )
                }
            } catch (e: Exception) {
                logger.error("Login database error", e)
                call.respond(HttpStatusCode.InternalServerError, ErrorResponse("Server login error: ${e.message}"))
            }
        }
    }
}
