// arduino/rover_control/rover_control.ino
// ─────────────────────────────────────────
// Road Rover – Motor Controller Firmware
//
// Listens on Serial (9600 baud) for single-byte commands from
// the Raspberry Pi and drives the L298N H-Bridge accordingly.
//
// Commands:
//   'F' → Forward     'B' → Backward
//   'L' → Turn Left   'R' → Turn Right
//   'S' → Stop
//
// L298N wiring (adjust pin numbers to match your board):
//   ENA ── Pin 5  (Left  motor PWM speed)
//   IN1 ── Pin 6  (Left  motor direction A)
//   IN2 ── Pin 7  (Left  motor direction B)
//   ENB ── Pin 10 (Right motor PWM speed)
//   IN3 ── Pin 8  (Right motor direction A)
//   IN4 ── Pin 9  (Right motor direction B)

// ── Pin definitions ───────────────────────────────────────────────────────────
const int ENA = 5;
const int IN1 = 6;
const int IN2 = 7;
const int IN3 = 8;
const int IN4 = 9;
const int ENB = 10;

// ── Speed (0-255) ─────────────────────────────────────────────────────────────
const int DRIVE_SPEED = 180;
const int TURN_SPEED  = 150;

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  motorStop();
  Serial.println("Road Rover Ready. Waiting for commands…");
}

// ── Main loop ─────────────────────────────────────────────────────────────────
void loop() {
  if (Serial.available() > 0) {
    char cmd = (char)Serial.read();

    switch (cmd) {
      case 'F': motorForward();  break;
      case 'B': motorBackward(); break;
      case 'L': motorLeft();     break;
      case 'R': motorRight();    break;
      case 'S': motorStop();     break;
      default:  break;   // ignore unknown bytes
    }
  }
}

// ── Motor primitives ──────────────────────────────────────────────────────────

void motorForward() {
  analogWrite(ENA, DRIVE_SPEED);
  analogWrite(ENB, DRIVE_SPEED);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void motorBackward() {
  analogWrite(ENA, DRIVE_SPEED);
  analogWrite(ENB, DRIVE_SPEED);
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void motorLeft() {
  analogWrite(ENA, TURN_SPEED);
  analogWrite(ENB, TURN_SPEED);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void motorRight() {
  analogWrite(ENA, TURN_SPEED);
  analogWrite(ENB, TURN_SPEED);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void motorStop() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}
