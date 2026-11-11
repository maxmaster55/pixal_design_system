// Square switch: a square track and a square thumb that moves in three held steps.
//   GgSwitch { checked: true; onToggled: v => apply(v) }
import QtQuick

Item {
    id: root
    property bool checked: false
    property color onColor: Glowgrid.accent
    signal toggled(bool value)
    width: 44; height: 22

    Rectangle { anchors.fill: parent; color: root.checked ? root.onColor : Glowgrid.stone; border.width: 2; border.color: Glowgrid.black }
    Rectangle {
        y: 4; width: 14; height: 14
        // three positions: off, halfway, on. `step` walks between them on a timer.
        x: 4 + root.step * 11
        color: root.checked ? Glowgrid.ink : Glowgrid.textSoft
    }
    property int step: checked ? 2 : 0
    onCheckedChanged: walk.restart()
    Timer {
        id: walk
        interval: Glowgrid.toggleMs / 3; repeat: true
        onTriggered: {
            const target = root.checked ? 2 : 0;
            if (root.step === target) stop(); else root.step += root.step < target ? 1 : -1;
        }
    }
    MouseArea { anchors.fill: parent; onClicked: { root.checked = !root.checked; root.toggled(root.checked); } }
}
