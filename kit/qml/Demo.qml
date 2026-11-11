// Run with:  qml kit/qml/Demo.qml     (or qmlscene)
import QtQuick

Rectangle {
    width: 420; height: 300
    color: Glowgrid.bg
    Column {
        anchors.centerIn: parent
        spacing: 18
        GgPanel {
            width: 340; height: 150
            edge: Glowgrid.accent
            Column {
                spacing: 10
                Text { text: "Connected"; font.family: Glowgrid.display; font.weight: Font.Bold; font.pixelSize: 26; color: Glowgrid.glow1 }
                Row { spacing: 12; GgLabel { text: "Address" } GgValue { text: "100.84.12.7" } }
                Row {
                    spacing: 14
                    GgSwitch { checked: true }
                    GgCells { value: 0.62; anchors.verticalCenter: parent.verticalCenter }
                    GgIcon { bits: ["0001000", "0011100", "0101010", "0001000", "0001000", "0001000", "0001000"]; color: Glowgrid.accent; anchors.verticalCenter: parent.verticalCenter }
                }
            }
        }
        Row { spacing: 14; GgButton { text: "Primary"; primary: true } GgButton { text: "Default" } }
    }
}
