#define NUM_BUTTONS 6
// GREEN: Top
// WHITE: B
// WHITEB: RIGHT
// BLACK: BOTTOM
// RED: LEFT
// BLACKB: A
// ORANGE: !GND
const int buttonPins[NUM_BUTTONS] = {33, 25, 26, 27, 14, 12};
enum ButtonIndex { A, LEFT, BOTTOM, RIGHT, B, TOP };

struct FCJData {
  int states[NUM_BUTTONS];
};

FCJData fcj_data;

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
}

FCJData readButtonStates() {
  FCJData data;
  for (int i = 0; i < NUM_BUTTONS; i++) {
    data.states[i] = !digitalRead(buttonPins[i]);
  }
  return data;
}

void loop() {
  fcj_data = readButtonStates();
  String output = String(fcj_data.states[LEFT]) +
                  String(fcj_data.states[RIGHT]) +
                  String(fcj_data.states[TOP]) +
                  String(fcj_data.states[BOTTOM]) +
                  String(fcj_data.states[A]) +
                  String(fcj_data.states[B]);
  Serial.println(output);
  delay(8);
}
