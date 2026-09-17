package ai.myfy.gateway.models

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty

@JsonIgnoreProperties(ignoreUnknown = true)
data class RegisterRequest(
    val email: String? = null,
    val name: String? = null,
    val password: String? = null,
    @JsonProperty("monthly_income") val monthlyIncome: Double? = 0.0,
    val currency: String? = "INR"
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class LoginRequest(
    val email: String? = null,
    val password: String? = null
)

data class AuthResponse(
    @JsonProperty("access_token") val accessToken: String,
    @JsonProperty("user_id") val userId: Long,
    val name: String,
    val email: String
)

data class ErrorResponse(
    val detail: String
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class NotificationDeliveryRequest(
    @JsonProperty("user_id") val userId: Long? = null,
    val title: String? = "",
    val message: String? = "",
    val content: String? = ""
)

data class NotificationDeliveryResponse(
    val success: Boolean,
    val delivered: Boolean
)
