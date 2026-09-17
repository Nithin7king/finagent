package ai.myfy.gateway.auth

import ai.myfy.gateway.config.EnvConfig
import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import com.auth0.jwt.interfaces.DecodedJWT
import java.util.Date

object JwtService {
    private val algorithm: Algorithm by lazy {
        Algorithm.HMAC256(EnvConfig.jwtSecret)
    }

    private val verifier by lazy {
        JWT.require(algorithm).build()
    }

    fun createToken(userId: Long, email: String): String {
        val now = System.currentTimeMillis()
        val expiryMillis = now + (EnvConfig.jwtExpiryHours * 3600 * 1000)

        return JWT.create()
            .withSubject(userId.toString())
            .withClaim("email", email)
            .withIssuedAt(Date(now))
            .withExpiresAt(Date(expiryMillis))
            .sign(algorithm)
    }

    fun verifyToken(token: String): DecodedJWT? {
        return try {
            verifier.verify(token)
        } catch (e: Exception) {
            null
        }
    }
}
