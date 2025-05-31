#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <WebSocketsClient.h>
#include <WebSocketsServer.h>
#include <string>
#include <ArduinoJson.h>

#define CMD_RECEIVE_WIFI_INFO 5
#define CMD_SEND_WIFI_INFO 1
#define CMD_RECEIVE_ACK 10

enum State {
  STATE_CONFIG_WIFI,
  STATE_SEND_WIFI_INFO,
  STATE_TURN_OFF_SERVER,
  STATE_CONNECT_WEBSOCKET,
  STATE_FORWARDING
};
State state = STATE_CONFIG_WIFI;

// declare Async server
AsyncWebServer* HTTPserver = new AsyncWebServer(80);
AsyncWebSocket* Node_Gateway_Async = new AsyncWebSocket("/ws");

// declare Sync client
WebSocketsClient webSocket;
const char *websocket_host = "18.141.13.46";
const uint16_t websocket_port = 8000;
const char *websocket_path = "/ws/image";

// declare Sync server
WebSocketsServer Node_Gateway(80);

std::vector<uint8_t> frame;

StaticJsonDocument<200> message;

// declare global variable
bool ready[2] = {0, 0};

char ssid[20]     = "ESP32_Gateway";
char password[20] = "12345678";

// 
String latestPayload = "";
bool newMessage = false;

// declare flag
bool message_wifi_flag = false;
bool message_ack_flag = false;
bool sending_client = true;
bool captured_image_flag = false;
bool server_connected_flag = false;
bool server_sending_flag = false;

const char htmlPage[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Wi-Fi Scan</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f0f0f0; }
    h1 { text-align: center; margin-bottom: 20px; }
    form { background: #fff; padding: 20px; border-radius: 10px; display: flex; flex-direction: column; gap: 10px; width: 90%; max-width: 350px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    label { font-weight: bold; }
    input { padding: 10px; font-size: 16px; border-radius: 5px; border: 1px solid #ccc; }
    button { padding: 10px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; }
    #wifi-list { list-style: none; padding: 0; width: 90%; max-width: 350px; margin-bottom: 20px; }
    #wifi-list li { padding: 10px; background-color: #ddd; margin: 5px 0; border-radius: 5px; text-align: center; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Nhập thông tin Wi-Fi</h1>
  <form id="wifi-form">
    <label for="ssid">Tên Wi-Fi (SSID):</label>
    <input type="text" id="ssid" name="ssid" required>
    <label for="password">Mật khẩu:</label>
    <input type="password" id="password" name="password" placeholder="(Để trống nếu không có mật khẩu)">
    <button type="submit">Kết nối</button>
  </form>
  <script>
  const baseURL = "http://192.168.4.1";

  class FastHttp {
      async send(method, url, body) {
          let response = await fetch(url, {
              method: method,
              headers: {
                  "Content-Type": "application/json",
              },
              body: body ? JSON.stringify(body) : null,
          });

          if (response.ok) {
              const contentType = response.headers.get("content-type");
              if (contentType && contentType.includes("application/json")) {
                  return response.json();
              } else {
                  return response.text(); // Nếu không phải JSON, trả về dạng text
              }
          } else {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
      }

      get(url) {
          return this.send("GET", url, null);
      }

      post(url, body) {
          return this.send("POST", url, body);
      }

      put(url, body) {
          return this.send("PUT", url, body);
      }

      delete(url) {
          return this.send("DELETE", url, null);
      }
  }

  const http = new FastHttp();

  document.getElementById('wifi-form').addEventListener('submit', async function(event) {
      event.preventDefault();

      const ssid = document.getElementById('ssid').value.trim();
      const password = document.getElementById('password').value.trim();

      const cmd = 5;
      const message = { cmd, ssid, password };

      console.log("Sending WiFi config:", message);

      try {
          const response = await http.post(baseURL + "/configwifi", message);
          console.log("Server response:", response);

          alert("WiFi config sent successfully!");
      } catch (err) {
          console.error("Error sending WiFi config:", err);
          alert("Failed to send WiFi config. Check console for details.");
      }
  });

  </script>
</body>
</html>
)rawliteral";

// declare function
void onWebSocketMessage(void *arg, uint8_t *data, size_t len); // gateway <-> node 
void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
             AwsEventType type, void *arg, uint8_t *data, size_t len); 
void serverEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length);
int connectToWiFi(const char* ssid, const char* password);
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length); //gateway - node
void sendWiFiInfo(AsyncWebSocket *ws);
void setup() {
  Serial.begin(115200);

  // turn on AP mode
  IPAddress local_IP(192, 168, 4, 1);
  IPAddress gateway_IP(192, 168, 4, 1);
  IPAddress subnet(255, 255, 255, 0);

  if (!WiFi.softAPConfig(local_IP, gateway_IP, subnet)) {
    Serial.println("AP config failed!");
  }

  WiFi.softAP(ssid, password);
  Serial.println("AP Mode started!");
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP());

  // WebSocket
  Node_Gateway_Async->onEvent(onEvent);
  HTTPserver->addHandler(Node_Gateway_Async);
  
  HTTPserver->on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send_P(200, "text/html", htmlPage); // Gửi HTML từ PROGMEM
  });

  HTTPserver->on("/configwifi", HTTP_POST,
    [](AsyncWebServerRequest *request){},
    NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      String body;
      for (size_t i = 0; i < len; i++) {
        body += (char)data[i];
      }
      DeserializationError error = deserializeJson(message, body);
      if(error){
      Serial.print("[Server] JSON error ");
      Serial.println(error.f_str());
      return; 
      }

      if(message["cmd"] == 5) message_wifi_flag = true;
      Serial.println("Nhận dữ liệu POST:");
      Serial.println(body);

      request->send(200, "application/json", "{\"status\":\"ok\"}");
  });

  HTTPserver->begin();
}

void loop() {
  switch (state)
  {
 // Serial.print  
  case STATE_CONFIG_WIFI:
    if(message_wifi_flag){
      strcpy(ssid, message["ssid"]);
      strcpy(password, message["password"]);

      if(connectToWiFi(ssid, password)){
        state = STATE_SEND_WIFI_INFO;
      }
      else{
        message_wifi_flag = false;
      }
    }
    // Serial.print("State: ");
    // Serial.println(state); 
    break;
  case STATE_SEND_WIFI_INFO:
    if(sending_client == true) {
      sendWiFiInfo(Node_Gateway_Async);
      sending_client = false;
    }
    if(message_ack_flag) {
      delay(200);
      state = STATE_TURN_OFF_SERVER;
    }
    // Serial.print("State: ");
    // Serial.println(state);
    break;
  case STATE_TURN_OFF_SERVER:
    delay(1000);
    if(Node_Gateway_Async) {
      Node_Gateway_Async->cleanupClients();
      Node_Gateway_Async->closeAll();
//      delete Node_Gateway_Async;
      Node_Gateway_Async = nullptr;
    }
    if(HTTPserver){
      HTTPserver->end();
//      delete HTTPserver;
      HTTPserver = nullptr;
    }

    WiFi.softAPdisconnect(true);
    Serial.println("AP mode stopped");
    state = STATE_CONNECT_WEBSOCKET;
    break;
  case STATE_CONNECT_WEBSOCKET:
    // Turn on websocket gateway - server
    webSocket.begin(websocket_host, websocket_port, websocket_path);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(2000);
    
    // Turn on websocket gateway - node

    Node_Gateway.begin();
    Node_Gateway.onEvent(serverEvent);
    
    delay(200);
    state = STATE_FORWARDING;
    Serial.print("State: ");
    Serial.println(state);
    break;
  case STATE_FORWARDING:    
    webSocket.loop();
    Node_Gateway.loop();

    // node send image data
    if(captured_image_flag && server_connected_flag) {
      webSocket.sendBIN(frame.data(), frame.size()); // send to server
      Serial.println("Gui den server.");
      captured_image_flag = false;
    }
    // {cmd : 2, servo:....}
    if(server_sending_flag){
      String jsonString;
      serializeJson(message, jsonString);
      Node_Gateway.broadcastTXT(jsonString);
      Serial.print("Sent Servo: ");
      Serial.println(jsonString);
      server_sending_flag = false;
    }
    
    break;
  default:
    break;
  }
}

// Node send message Async
void onWebSocketMessage(void *arg, uint8_t *data, size_t len) {
  AwsFrameInfo *info = (AwsFrameInfo*)arg;

  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    String msg = "";
    for (size_t i = 0; i < len; i++) {
      msg += (char)data[i];
    }

    Serial.print("Client send: ");
    Serial.println(msg);

    // Parse JSON
    DeserializationError error = deserializeJson(message, msg);
    if(error){
      Serial.print("JSON error ");
      Serial.println(error.f_str());
      return;
    }

    if(message["cmd"] == 10){
      if(message["device"] == 0) ready[0] = 1;
      if(message["device"] == 1) ready[1] = 1;

      if(ready[0] && ready[1]) message_ack_flag = 1;
    }

    
  Node_Gateway_Async->textAll("{\"gateway\": \"hello node\"}");
  }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client,
             AwsEventType type, void *arg, uint8_t *data, size_t len) {
  switch (type) {
    case WS_EVT_CONNECT:
      Serial.printf("Client %u connect to\n", client->id());
      break;
    case WS_EVT_DISCONNECT:
      Serial.printf("Client %u disconnect to\n", client->id());
      break;
    case WS_EVT_DATA:{
      AwsFrameInfo *info = (AwsFrameInfo *)arg;

      switch (info->opcode){
      case WS_TEXT:
        onWebSocketMessage(arg, data, len);
        break;
      case WS_BINARY:
        Serial.printf("[ASYNCS] Đã nhận %d byte dữ liệu nhị phân từ client #%u\n", len, client->id());
        captured_image_flag = true;
        frame.assign(data, data + len);  // sao chép an toàn toàn bộ dữ liệu tvào frame
      default:
        break;
      }
    }
      break;
    default:
      break;
  }
}

// Node send message Sync
void serverEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
  switch(type) {
    case WStype_TEXT:
      Serial.printf("[Gateway] Received from node: %s\n", payload);
      latestPayload = String((char*)payload);
      newMessage = true;
      break;
    case WStype_BIN:
      //Serial.printf("Đã nhận %d byte dữ liệu nhị phân từ client #%u\n", length);
      captured_image_flag = true;
      frame.assign(payload, payload + length);  
      break;
  }
  // // Kiểm tra nếu payload chứa {"device": "esp-1"}
  //   StaticJsonDocument<200> doc;
  //   DeserializationError error = deserializeJson(doc, payload);
  //   if (!error && doc.containsKey("device") && doc["device"] != "") {
  //     node_connected = true;
  //     char doc["device"]
  //     Serial.println("[Gateway] Node esp-1 connected successfully!");
  //   }
  //   else if (type == WStype_DISCONNECTED) {
  //   Serial.printf("[Gateway] Node %u disconnected\n", num);
  //   node_connected = false; // Reset cờ khi node ngắt kết nối
  // }
}

int connectToWiFi(const char* ssid, const char* password){
  WiFi.disconnect(true);
  delay(200);
  // connect to wifi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wifi");

  // waiting over 5s will give up
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED) {
    if(timeout == 5) return 0;
    delay(500);
    Serial.print(".");
    timeout = timeout + 0.5;
  }

  Serial.print(WiFi.SSID());
  Serial.println(" connected!");
  return 1;
}

// server send message
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("[WS] Connected to server");
      //webSocket.sendTXT("{\"gateway\": \"hello Server\"}"); 
      server_connected_flag = true;
      break;

    case WStype_DISCONNECTED:
      Serial.println("[WS] Disconnected to server");
      server_connected_flag = false;
      break;

    case WStype_TEXT:
      Serial.printf("[WS] Received from server: %s\n", payload);
      
      DeserializationError error = deserializeJson(message, payload);
      if(error){
        Serial.print("JSON error ");
        Serial.println(error.f_str());
        return;
      }

      if(message["cmd"] == 2) server_sending_flag = true;

      break;
  }
}

void sendWiFiInfo(AsyncWebSocket *ws) {
  StaticJsonDocument<200> doc;
  doc["cmd"] = CMD_SEND_WIFI_INFO; // CMD_SEND_WIFI_INFO = 1
  doc["ssid"] = ssid;
  doc["password"] = password;
  doc["IP"] = WiFi.localIP().toString();

  String jsonString;
  serializeJson(doc, jsonString);
  
  ws->textAll(jsonString);
  Serial.print("Sent WiFi info: ");
  Serial.println(jsonString);
}
