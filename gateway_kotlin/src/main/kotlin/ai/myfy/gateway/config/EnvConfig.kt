package ai.myfy.gateway.config

import io.github.cdimascio.dotenv.Dotenv
import java.io.File

object EnvConfig {
    private val dotenv: Dotenv? = try {
        val rootDir = File(".").canonicalFile
        val parentDir = rootDir.parentFile

        when {
            File(rootDir, ".env").exists() -> Dotenv.configure().directory(rootDir.absolutePath).load()
            File(rootDir, "gateway/.env").exists() -> Dotenv.configure().directory(File(rootDir, "gateway").absolutePath).load()
            parentDir != null && File(parentDir, ".env").exists() -> Dotenv.configure().directory(parentDir.absolutePath).load()
            else -> Dotenv.configure().ignoreIfMissing().load()
        }
    } catch (e: Exception) {
        null
    }

    fun get(key: String, defaultValue: String = ""): String {
        return System.getenv(key) ?: dotenv?.get(key) ?: defaultValue
    }

    val port: Int by lazy { get("PORT", "5000").toIntOrNull() ?: 5000 }
    val fastApiUrl: String by lazy { get("FASTAPI_BACKEND_URL", "http://localhost:8000").trimEnd('/') }
    val jwtSecret: String by lazy { get("JWT_SECRET", "finagent-jwt-secret-change-me") }
    val jwtExpiryHours: Long by lazy { get("JWT_EXPIRY_HOURS", "24").toLongOrNull() ?: 24L }
    val databaseUrl: String by lazy {
        get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finagent")
    }
}
