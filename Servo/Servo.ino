#include <WiFi.h>
#include <string.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

#define MAX_LEFT -400
#define MAX_RIGHT 400
#define MAX_UP 400
#define MAX_DOWN -400
Servo ServoLR;
Servo ServoUD;

#define CMD_WIFI  1
#define CMD_SERVO 2

char deviceName[20] = "esp32-node2"; 

enum Mode {
    MODE_WIFI_CONFIG,
    MODE_WEBSOCKET_CONFIG,
    MODE_PROCESSING
};

Mode mode = MODE_WIFI_CONFIG;

WebSocketsClient webSocket;

char websocket_host[20] = "192.168.4.1";
const uint16_t websocket_port = 80;
const char* websocket_path = "/ws";

StaticJsonDocument<200> doc;

char ssid[50] = "ESP32_Gateway";
char password[50] = "12345678";
int servoAction = 0;

unsigned long startTime = 0;
int intervalTime = 100;      // thời gian quay (ms)
int static thresholdLR=0, thresholdUD=0;
bool running = false;

bool wifi_flag = true;
bool websocket_initialized = false;
bool servo_flag = false;
int changing_wifi_time = 0;

//
void connectToWiFi(const char* ssid, const char* password);
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length);
void readGatewayMessage(char message[]);
void controlServo();

void setup() {
  Serial.begin(115200);
  ServoLR.attach(25);  // LR
  ServoUD.attach(26);  // UD
  ServoLR.write(90);   // Dừng mặc định
  ServoUD.write(90);
  delay(1000);
}

void loop() {
  webSocket.loop();  // Luôn chạy WebSocket vòng lặp

  switch(mode) {
    case MODE_WIFI_CONFIG:
      if (wifi_flag) {
        delay(500);
        webSocket.disconnect();
        websocket_initialized = false;

        connectToWiFi(ssid, password);

        wifi_flag = false;
        changing_wifi_time++;
        mode = MODE_WEBSOCKET_CONFIG;
      }
      break;

    case MODE_WEBSOCKET_CONFIG:
      if (!websocket_initialized) {
      //  delay(1000);
        Serial.print(websocket_host);
        Serial.print("  ");
        Serial.print(websocket_port);
        Serial.print("  ");
        Serial.print(websocket_path);
        Serial.println("  ");
        webSocket.begin(websocket_host, websocket_port, websocket_path);
        webSocket.onEvent(webSocketEvent);
        webSocket.setReconnectInterval(4000);
        websocket_initialized = true;

      if (changing_wifi_time == 1)
        mode = MODE_WEBSOCKET_CONFIG;
      else
        mode = MODE_PROCESSING;
      }

    case MODE_PROCESSING:
      if(servo_flag){
        controlServo();
        // Serial.print("LR: ");
        // Serial.print(ServoLR.read());
        // Serial.print("   UD: ");
        // Serial.println(ServoUD.read());
        
        StaticJsonDocument<100> sendDoc;
        sendDoc["lr"] = ServoLR.read();
        sendDoc["ud"] = ServoUD.read();
        char buffer[100];
        serializeJson(sendDoc, buffer);
        webSocket.sendTXT(buffer);
      }
      break;
    default:
      break;
  }
}

void connectToWiFi(const char* ssid, const char* password){
  WiFi.disconnect(true);
  delay(200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wifi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.print("\n");
  Serial.print(WiFi.SSID());
  Serial.println(" connected!");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("[WebSocket] Connected to Gateway.");
      webSocket.sendTXT("{\"device\": \"esp-2\"}");
      break;

    case WStype_DISCONNECTED:
      Serial.println("[WebSocket] Disconnected to gateway.");
      break;

    case WStype_TEXT:
      Serial.printf("[WebSocket] Got message: %s\n", payload);
      readGatewayMessage((char*)payload);
      break;
      
    default:
      break;
  }
}

void readGatewayMessage(char json[]) {
  //Serial.println(json);
  DeserializationError err = deserializeJson(doc, json);
  if (err) {
    Serial.print("Lỗi JSON: ");
    Serial.println(err.f_str());
    return;
  }

  int cmd = doc["cmd"];
  switch(cmd) {
    case CMD_WIFI:
      strcpy(ssid, doc["ssid"]);
      strcpy(password, doc["password"]);
      strcpy(websocket_host, doc["IP"]);
      Serial.printf("ssid: %s | password: %s\n", ssid, password);
      delay(200);
      webSocket.sendTXT("{\"cmd\": 10, \"device\": 1}");
      Serial.printf("Sent cmd: 10, device: 1");
      delay(1000);
      
      wifi_flag = true;
      mode = MODE_WIFI_CONFIG;
      
    //  websocket_initialized = false; // Để kết nối lại WebSocket ở IP mới
      break;

    case CMD_SERVO:
      servoAction = doc["servo"];
      Serial.printf("Servo: %d\n", servoAction);
      servo_flag = true;
      break;

    default:
      break;
  }
}

void controlServo() {
  int clockwise = servoAction;

  // Nếu chưa quay → bắt đầu
  if (!running) {
    if (clockwise == 6 && thresholdLR < MAX_RIGHT) {
      thresholdLR += intervalTime;
      ServoLR.write(105);  // quay phải
      Serial.println("RIGHT");
    }
    else if (clockwise == 4 && thresholdLR > MAX_LEFT) {
      thresholdLR -= intervalTime;
      ServoLR.write(79);   // quay trái
      Serial.println("LEFT");
    }
    else if (clockwise == 2 && thresholdUD > MAX_DOWN) {
      thresholdUD -= intervalTime;
      ServoUD.write(79);   // quay xuống
      Serial.println("DOWN");
    }
    else if (clockwise == 8 && thresholdUD < MAX_UP) {
      thresholdUD += intervalTime;
      ServoUD.write(105);  // quay lên
      Serial.println("UP");
    }
    else
    {
      ServoUD.write(90);
      ServoLR.write(90);
    }

    startTime = millis();
    
    running = true;
  }

  // Nếu đang quay → kiểm tra thời gian dừng
  if (running && millis() - startTime >= intervalTime) {
    ServoLR.write(90);   // Dừng
    ServoUD.write(90);
    running = false;
    servo_flag = false;
  }
}