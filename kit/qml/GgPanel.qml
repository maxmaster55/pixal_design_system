// A Glowgrid panel: surface fill, 2px edge, hard offset shadow. Put content inside.
//   GgPanel { width: 300; GgLabel { text: "CPU" } }
import QtQuick

Item {
    id: root
    default property alias content: inner.data
    property int padding: 14
    /// "black" for cards, "accent" for the thing that has the user's attention (popups, focus)
    property color edge: Glowgrid.black
    property int shadow: Glowgrid.shadowLg
    implicitWidth: inner.childrenRect.width + padding * 2
    implicitHeight: inner.childrenRect.height + padding * 2

    Rectangle { x: root.shadow; y: root.shadow; width: parent.width; height: parent.height; color: Glowgrid.black }
    Rectangle { anchors.fill: parent; color: Glowgrid.surface; border.width: Glowgrid.borderFocus; border.color: root.edge }
    Item { id: inner; anchors.fill: parent; anchors.margins: root.padding }
}
