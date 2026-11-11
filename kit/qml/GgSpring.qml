// A spring whose output lands on the pixel grid. Same solver and presets as weave-motion.
//   GgSpring { id: x; preset: "expressive"; target: open ? 200 : 0 }
//   Rectangle { x: x.value }          // value is already rounded to `grid`
// Changing `target` mid-flight keeps position and velocity.
import QtQuick

Item {
    id: root
    property real target: 0
    /// "fast", "default", "expressive" or "gentle"
    property string preset: "default"
    /// the pixel quantum; 1 gives whole pixels, 0 the raw spring
    property real grid: 2
    /// the grid-snapped value to bind to
    readonly property real value: grid > 0 ? Math.round(raw / grid) * grid : raw
    // Not bound to `target`: a binding would make the value jump there. It starts at the
    // initial target (set once, below) and from then on only the solver moves it.
    property real raw: 0
    property real velocity: 0
    property bool ready: false
    Component.onCompleted: { raw = target; ready = true; }
    readonly property bool moving: clock.running
    signal settled()

    readonly property var presets: ({ fast: [500, 0.85], "default": [300, 0.8], expressive: [220, 0.65], gentle: [140, 1.0] })

    onTargetChanged: if (ready) clock.running = true
    function snapTo(v) { raw = v; velocity = 0; clock.running = false; }

    // exact solution of the damped spring over dt seconds (mass 1), as in weave-core
    function step(dt) {
        const p = presets[preset] || presets["default"], k = p[0], zeta = p[1];
        const omega = Math.sqrt(k), y0 = raw - target, v0 = velocity;
        let y, v;
        if (zeta < 0.9999) {
            const alpha = zeta * omega, wd = omega * Math.sqrt(1 - zeta * zeta), B = (v0 + alpha * y0) / wd;
            const e = Math.exp(-alpha * dt), c = Math.cos(wd * dt), s = Math.sin(wd * dt);
            y = e * (y0 * c + B * s);
            v = e * ((B * wd - alpha * y0) * c + (-y0 * wd - alpha * B) * s);
        } else {
            const B = v0 + omega * y0, e = Math.exp(-omega * dt);
            y = (y0 + B * dt) * e;
            v = (B - omega * (y0 + B * dt)) * e;
        }
        if (Math.abs(y) < 0.01 && Math.abs(v) < 0.01) { raw = target; velocity = 0; clock.running = false; settled(); }
        else { raw = target + y; velocity = v; }
    }

    Timer {
        id: clock
        interval: 16; repeat: true
        property real last: 0
        onRunningChanged: last = Date.now()
        onTriggered: { const now = Date.now(); root.step(Math.min(0.064, (now - last) / 1000)); last = now; }
    }
}
