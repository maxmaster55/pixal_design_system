// A 7x7 one-bit pixel icon. `bits` is seven strings of seven '0'/'1' characters, as in
// kit/icons/icons.json. `cell` is screen pixels per art pixel (2 gives a 14px icon).
//   GgIcon { bits: ["0001000","0011100","0101010","0001000","0001000","0001000","0001000"]; color: Glowgrid.accent }
import QtQuick

Item {
    id: root
    property var bits: []
    property int cell: 2
    property color color: Glowgrid.textSoft
    width: 7 * cell
    height: 7 * cell

    Repeater {
        model: 49
        Rectangle {
            required property int index
            readonly property int col: index % 7
            readonly property int row: Math.floor(index / 7)
            x: col * root.cell; y: row * root.cell
            width: root.cell; height: root.cell
            color: root.color
            visible: root.bits.length === 7 && root.bits[row].charAt(col) === "1"
        }
    }
}
