package ai.myfy.gateway.auth

import org.mindrot.jbcrypt.BCrypt

object PasswordService {
    fun hashPassword(password: String): String {
        return BCrypt.hashpw(password, BCrypt.gensalt(12))
    }

    fun verifyPassword(password: String, hashed: String): Boolean {
        return try {
            val normalizedHash = if (hashed.startsWith("\$2b\$") || hashed.startsWith("\$2y\$")) {
                "\$2a\$" + hashed.substring(4)
            } else {
                hashed
            }
            BCrypt.checkpw(password, normalizedHash)
        } catch (e: Exception) {
            false
        }
    }
}
