package ai.myfy.gateway.config

import com.zaxxer.hikari.HikariConfig
import com.zaxxer.hikari.HikariDataSource
import java.io.File
import java.net.URI
import java.sql.Connection
import org.slf4j.LoggerFactory

private val logger = LoggerFactory.getLogger("DatabaseConfig")

object DatabaseConfig {
    private val dataSource: HikariDataSource by lazy {
        val rawUrl = EnvConfig.databaseUrl

        // Try primary PostgreSQL connection if configured
        if (rawUrl.startsWith("postgresql://") || rawUrl.startsWith("postgres://")) {
            try {
                val config = HikariConfig()
                config.driverClassName = "org.postgresql.Driver"

                val cleanUrl = rawUrl.replace("postgres://", "postgresql://")
                val uri = URI(cleanUrl)
                val host = uri.host
                val port = if (uri.port != -1) uri.port else 5432
                val path = uri.path.trimStart('/')
                val jdbcUrl = "jdbc:postgresql://$host:$port/$path"
                config.jdbcUrl = jdbcUrl

                val userInfo = uri.userInfo
                if (userInfo != null && userInfo.contains(":")) {
                    val parts = userInfo.split(":", limit = 2)
                    config.username = parts[0]
                    config.password = java.net.URLDecoder.decode(parts[1], "UTF-8")
                }

                config.maximumPoolSize = 10
                config.minimumIdle = 2
                config.idleTimeout = 30000
                config.connectionTimeout = 3000
                config.isAutoCommit = true

                val ds = HikariDataSource(config)
                // Test connectivity immediately
                ds.connection.use { conn ->
                    val stmt = conn.createStatement()
                    stmt.executeQuery("SELECT 1")
                }
                logger.info("Connected successfully to PostgreSQL database.")
                return@lazy ds
            } catch (e: Exception) {
                logger.warn("PostgreSQL not reachable (${e.message}). Falling back to local SQLite.")
            }
        }

        // Fallback to SQLite (finagent.db in project root or current dir)
        val config = HikariConfig()
        val sqlitePath = when {
            File("finagent.db").exists() -> File("finagent.db").absolutePath
            File("../finagent.db").exists() -> File("../finagent.db").absolutePath
            else -> File("finagent.db").absolutePath
        }

        config.driverClassName = "org.sqlite.JDBC"
        config.jdbcUrl = "jdbc:sqlite:$sqlitePath"
        config.maximumPoolSize = 5
        config.connectionTimeout = 10000
        config.isAutoCommit = true

        logger.info("Connected to local SQLite database: $sqlitePath")
        HikariDataSource(config)
    }

    fun getConnection(): Connection = dataSource.connection

    fun close() {
        if (!dataSource.isClosed) {
            dataSource.close()
        }
    }
}
