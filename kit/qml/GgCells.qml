// Progress or level as square cells, never a smooth bar.
//   GgCells { value: 0.62 }            16 cells, 10 lit
//   GgCells { count: 4; value: wifi / 100; rising: true; color: Glowgrid.glow3 }   signal bars
import QtQuick

Row {
    id: root
    property real value: 0          // 0..1
    property int count: 16
    property color color: Glowgrid.accent
    property int cellWidth: 6
    property int cellHeight: 8
    /// each cell taller than the last, like signal-strength bars
    property bool rising: false
    spacing: 2

    Repeater {
        model: root.count
        Item {
            required property int index
            width: root.cellWidth; height: root.cellHeight
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: root.rising ? Math.round(parent.height * (index + 1) / root.count) : parent.height
                color: index < Math.floor(root.value * root.count + 0.0001) ? root.color : Glowgrid.stone
            }
        }
    }
}
