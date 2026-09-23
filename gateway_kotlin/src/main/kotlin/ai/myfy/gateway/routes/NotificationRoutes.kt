package ai.myfy.gateway.routes

import ai.myfy.gateway.models.NotificationDeliveryRequest
import ai.myfy.gateway.models.NotificationDeliveryResponse
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.call
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.post
import io.ktor.server.routing.route
import org.slf4j.LoggerFactory

private val logger = LoggerFactory.getLogger("NotificationDelivery")

fun Route.notificationRoutes() {
    route("/notifications") {
        post("/deliver") {
            val req = try {
                call.receive<NotificationDeliveryRequest>()
            } catch (e: Exception) {
                NotificationDeliveryRequest()
            }

            println("\n=========================================")
            println("🚀 [KOTLIN NOTIFICATION DELIVERY SYSTEM]")
            println("To User ID: ${req.userId}")
            println("Title:      ${req.title}")
            println("Message:    ${req.message}")
            println("Content:\n${req.content}")
            println("=========================================\n")

            call.respond(
                HttpStatusCode.OK,
                NotificationDeliveryResponse(success = true, delivered = true)
            )
        }
    }
}
