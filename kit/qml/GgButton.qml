// Text button with a hard 4px shadow. Hover lifts it 2px, press sinks it into the shadow.
//   GgButton { text: "Save"; primary: true; onClicked: save() }
import QtQuick

Item {
    id: root
    property string text: ""
    property bool primary: false
    signal clicked()
    implicitWidth: lbl.implicitWidth + 26
    implicitHeight: 30

    readonly property int lift: area.pressed ? -2 : area.containsMouse ? 2 : 0
    Rectangle { x: Glowgrid.shadowMd; y: Glowgrid.shadowMd; width: parent.width; height: parent.height; color: Glowgrid.black }
    Rectangle {
        id: face
        x: -root.lift; y: -root.lift
        width: parent.width; height: parent.height
        color: root.primary || area.containsMouse ? Glowgrid.accent : Glowgrid.surface
        border.width: 1
        border.color: root.primary || area.containsMouse ? Glowgrid.black : Glowgrid.stone
        GgLabel { id: lbl; anchors.centerIn: parent; text: root.text; font.pixelSize: 11; color: root.primary || area.containsMouse ? Glowgrid.ink : Glowgrid.text }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; onClicked: root.clicked() }
}
