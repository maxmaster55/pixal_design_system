#!/usr/bin/env python3
"""Generate the three Glowgrid VS Code themes from one template.

    python3 generate.py            write themes/*.json, then validate and print contrast
    python3 generate.py --check    validate the files on disk and print contrast, write nothing

The lights per theme mirror ../shell/Theme.qml; the terminal colours mirror
../palettes/glowgrid-<theme>.json. In the template a value is either a literal
hex colour or "$name" / "$name/AA", where name is a palette key and AA is a hex
alpha byte. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The dark world, shared by every theme (Theme.qml; air and stone ramps from the design tokens).
WORLD = {
    "bg": "#0b0714",
    "air1": "#100a1b",
    "air2": "#150c22",
    "surface": "#170d24",
    "air3": "#1b1029",
    "air4": "#241433",
    "air5": "#2f1a44",
    "stone": "#3b2a3f",
    "stone2": "#5a3d52",
    "stoneLit": "#8a5a5a",
    "text": "#e9def0",
    "textSoft": "#a493b0",
    "ink": "#1c1226",
    "comment": "#9482ad",   # muted violet
    "property": "#cfc0e6",  # members and attribute names: text leaning violet
    "none": "#00000000",
}

# The lights. accent/hot/deep/glow1-3 come from Theme.qml, alert and term from the palettes.
# string and type are chosen per theme: the string light has to differ from the keyword light,
# and Frost's glow-2 (#e6fbff) is too close to body text to mark types, so Frost uses its
# terminal violet instead.
THEMES = {
    "ember": {
        "label": "Glowgrid Ember",
        "accent": "#ff8a2a", "hot": "#ffd36b", "deep": "#b24d0a",
        "glow1": "#7cf36b", "glow2": "#e94bd6", "glow3": "#4bc6e9",
        "alert": "#ff5f5f",
        "string": "#ffa565",    # warm: the accent, one step lighter
        "type": "#f06fe0",      # glow-2, lighter tint
        "typeSoft": "#ffb8f4",
        "term": {
            "black": "#170d24", "red": "#ff5f5f", "green": "#7cf36b", "yellow": "#ffd36b",
            "blue": "#4bc6e9", "magenta": "#e94bd6", "cyan": "#8fe3f7", "white": "#e9def0",
            "brightBlack": "#5a3d52", "brightRed": "#ff8a80", "brightGreen": "#b8ff9a",
            "brightYellow": "#ffe49c", "brightBlue": "#8fdcf5", "brightMagenta": "#ffb8f4",
            "brightCyan": "#bdf0ff", "brightWhite": "#ffffff",
        },
    },
    "forge": {
        "label": "Glowgrid Forge",
        "accent": "#ff9a3c", "hot": "#ffc56a", "deep": "#c25a12",
        "glow1": "#ffe08a", "glow2": "#f07a22", "glow3": "#bdf0ff",
        "alert": "#ff5f5f",
        "string": "#b4e06b",    # the forge terminal green: the one light that is not orange
        "type": "#f07a22",      # glow-2
        "typeSoft": "#ffab6b",
        "term": {
            "black": "#170d24", "red": "#ff5f5f", "green": "#b4e06b", "yellow": "#ffc56a",
            "blue": "#7cc8ff", "magenta": "#f07a22", "cyan": "#bdf0ff", "white": "#e9def0",
            "brightBlack": "#5a3d52", "brightRed": "#ff8a80", "brightGreen": "#d2f09a",
            "brightYellow": "#ffe08a", "brightBlue": "#a8dcff", "brightMagenta": "#ffab6b",
            "brightCyan": "#e0f8ff", "brightWhite": "#ffffff",
        },
    },
    "frost": {
        "label": "Glowgrid Frost",
        "accent": "#4bc6e9", "hot": "#bdf0ff", "deep": "#17607a",
        "glow1": "#8fe3f7", "glow2": "#e6fbff", "glow3": "#ffd36b",
        "alert": "#ff6b7a",
        "string": "#ffb38f",    # warm against the cold keywords
        "type": "#b9a4ff",      # terminal violet (glow-2 would read as body text)
        "typeSoft": "#d5c8ff",
        "term": {
            "black": "#170d24", "red": "#ff6b7a", "green": "#8fe3c0", "yellow": "#ffd36b",
            "blue": "#4bc6e9", "magenta": "#b9a4ff", "cyan": "#8fe3f7", "white": "#e9def0",
            "brightBlack": "#5a3d52", "brightRed": "#ff97a2", "brightGreen": "#b6f0d8",
            "brightYellow": "#ffe49c", "brightBlue": "#8fdcf5", "brightMagenta": "#d5c8ff",
            "brightCyan": "#e6fbff", "brightWhite": "#ffffff",
        },
    },
}

COLORS = {
    # base
    "focusBorder": "$accent",
    "foreground": "$text",
    "disabledForeground": "$stone2",
    "descriptionForeground": "$textSoft",
    "errorForeground": "$alert",
    "icon.foreground": "$textSoft",
    "selection.background": "$accent/55",
    "widget.shadow": "$none",
    "widget.border": "$stone",
    "sash.hoverBorder": "$accent",
    "textLink.foreground": "$glow3",
    "textLink.activeForeground": "$hot",
    "textPreformat.foreground": "$glow1",
    "textPreformat.background": "$air4",
    "textBlockQuote.background": "$surface",
    "textBlockQuote.border": "$stone",
    "textCodeBlock.background": "$ink",
    "textSeparator.foreground": "$stone",
    "toolbar.hoverBackground": "$stone",
    "toolbar.activeBackground": "$stone2",

    # editor
    "editor.background": "$bg",
    "editor.foreground": "$text",
    "editorCursor.foreground": "$accent",
    "editorCursor.background": "$bg",
    "editorLineNumber.foreground": "$stone2",
    "editorLineNumber.activeForeground": "$hot",
    "editorLineNumber.dimmedForeground": "$stone",
    "editor.lineHighlightBackground": "$surface",
    "editor.lineHighlightBorder": "$none",
    "editor.selectionBackground": "$accent/40",
    "editor.inactiveSelectionBackground": "$accent/22",
    "editor.selectionHighlightBackground": "$accent/26",
    "editor.selectionHighlightBorder": "$none",
    "editor.wordHighlightBackground": "$glow3/26",
    "editor.wordHighlightStrongBackground": "$glow2/30",
    "editor.wordHighlightTextBackground": "$glow3/20",
    "editor.findMatchBackground": "$hot/66",
    "editor.findMatchBorder": "$hot",
    "editor.findMatchHighlightBackground": "$hot/30",
    "editor.findMatchHighlightBorder": "$none",
    "editor.findRangeHighlightBackground": "$air4/99",
    "editor.rangeHighlightBackground": "$air4/80",
    "editor.hoverHighlightBackground": "$glow3/22",
    "editor.linkedEditingBackground": "$glow2/26",
    "editor.foldBackground": "$air4/80",
    "editor.stackFrameHighlightBackground": "$hot/26",
    "editor.focusedStackFrameHighlightBackground": "$glow1/26",
    "editor.snippetTabstopHighlightBackground": "$air5",
    "editor.snippetFinalTabstopHighlightBorder": "$glow1",
    "editorLink.activeForeground": "$glow3",
    "editorWhitespace.foreground": "$stone",
    "editorIndentGuide.background1": "$air4",
    "editorIndentGuide.activeBackground1": "$stone2",
    "editorRuler.foreground": "$air4",
    "editorCodeLens.foreground": "$comment",
    "editorInlayHint.foreground": "$comment",
    "editorInlayHint.background": "$surface",
    "editorGhostText.foreground": "$stoneLit",
    "editorLightBulb.foreground": "$hot",
    "editorLightBulbAutoFix.foreground": "$glow1",
    "editorBracketMatch.background": "$accent/30",
    "editorBracketMatch.border": "$accent",
    "editorBracketHighlight.foreground1": "$hot",
    "editorBracketHighlight.foreground2": "$glow2",
    "editorBracketHighlight.foreground3": "$glow3",
    "editorBracketHighlight.foreground4": "$glow1",
    "editorBracketHighlight.foreground5": "$accent",
    "editorBracketHighlight.foreground6": "$typeSoft",
    "editorBracketHighlight.unexpectedBracket.foreground": "$alert",
    "editorBracketPairGuide.activeBackground1": "$hot/80",
    "editorBracketPairGuide.activeBackground2": "$glow2/80",
    "editorBracketPairGuide.activeBackground3": "$glow3/80",
    "editorBracketPairGuide.activeBackground4": "$glow1/80",
    "editorBracketPairGuide.activeBackground5": "$accent/80",
    "editorBracketPairGuide.activeBackground6": "$typeSoft/80",
    "editorBracketPairGuide.background1": "$hot/30",
    "editorBracketPairGuide.background2": "$glow2/30",
    "editorBracketPairGuide.background3": "$glow3/30",
    "editorBracketPairGuide.background4": "$glow1/30",
    "editorBracketPairGuide.background5": "$accent/30",
    "editorBracketPairGuide.background6": "$typeSoft/30",
    "editorError.foreground": "$alert",
    "editorWarning.foreground": "$hot",
    "editorInfo.foreground": "$glow3",
    "editorHint.foreground": "$glow1",
    "editorUnnecessaryCode.opacity": "#000000aa",

    # gutter
    "editorGutter.background": "$bg",
    "editorGutter.addedBackground": "$glow1",
    "editorGutter.modifiedBackground": "$glow3",
    "editorGutter.deletedBackground": "$alert",
    "editorGutter.foldingControlForeground": "$textSoft",
    "editorGutter.commentRangeForeground": "$stone2",

    # overview ruler and minimap
    "editorOverviewRuler.border": "$none",
    "editorOverviewRuler.background": "$bg",
    "editorOverviewRuler.findMatchForeground": "$hot/cc",
    "editorOverviewRuler.selectionHighlightForeground": "$accent/aa",
    "editorOverviewRuler.wordHighlightForeground": "$glow3/aa",
    "editorOverviewRuler.wordHighlightStrongForeground": "$glow2/aa",
    "editorOverviewRuler.bracketMatchForeground": "$accent",
    "editorOverviewRuler.errorForeground": "$alert",
    "editorOverviewRuler.warningForeground": "$hot",
    "editorOverviewRuler.infoForeground": "$glow3",
    "editorOverviewRuler.addedForeground": "$glow1/cc",
    "editorOverviewRuler.modifiedForeground": "$glow3/cc",
    "editorOverviewRuler.deletedForeground": "$alert/cc",
    "minimap.background": "$bg",
    "minimap.findMatchHighlight": "$hot",
    "minimap.selectionHighlight": "$accent",
    "minimap.selectionOccurrenceHighlight": "$accent/aa",
    "minimap.errorHighlight": "$alert",
    "minimap.warningHighlight": "$hot",
    "minimap.foregroundOpacity": "#000000cc",
    "minimapSlider.background": "$stone/66",
    "minimapSlider.hoverBackground": "$stone2/88",
    "minimapSlider.activeBackground": "$accent/66",
    "minimapGutter.addedBackground": "$glow1",
    "minimapGutter.modifiedBackground": "$glow3",
    "minimapGutter.deletedBackground": "$alert",

    # editor widgets (find, hover, suggest)
    "editorWidget.background": "$surface",
    "editorWidget.foreground": "$text",
    "editorWidget.border": "$stone",
    "editorWidget.resizeBorder": "$accent",
    "editorHoverWidget.background": "$surface",
    "editorHoverWidget.foreground": "$text",
    "editorHoverWidget.border": "$stone",
    "editorHoverWidget.statusBarBackground": "$air4",
    "editorSuggestWidget.background": "$surface",
    "editorSuggestWidget.border": "$stone",
    "editorSuggestWidget.foreground": "$text",
    "editorSuggestWidget.highlightForeground": "$hot",
    "editorSuggestWidget.focusHighlightForeground": "$hot",
    "editorSuggestWidget.selectedBackground": "$stone",
    "editorSuggestWidget.selectedForeground": "$text",
    "editorStickyScroll.background": "$bg",
    "editorStickyScrollHover.background": "$surface",
    "editorStickyScroll.border": "$stone",
    "editorStickyScroll.shadow": "$none",
    "editorMarkerNavigation.background": "$surface",
    "editorMarkerNavigationError.background": "$alert",
    "editorMarkerNavigationWarning.background": "$hot",
    "editorMarkerNavigationInfo.background": "$glow3",

    # peek view
    "peekView.border": "$accent",
    "peekViewTitle.background": "$air4",
    "peekViewTitleLabel.foreground": "$hot",
    "peekViewTitleDescription.foreground": "$textSoft",
    "peekViewEditor.background": "$air1",
    "peekViewEditorGutter.background": "$air1",
    "peekViewEditor.matchHighlightBackground": "$hot/40",
    "peekViewEditor.matchHighlightBorder": "$none",
    "peekViewResult.background": "$surface",
    "peekViewResult.fileForeground": "$text",
    "peekViewResult.lineForeground": "$textSoft",
    "peekViewResult.matchHighlightBackground": "$hot/40",
    "peekViewResult.selectionBackground": "$stone",
    "peekViewResult.selectionForeground": "$text",

    # diff editor: added = glow-1 tint, removed = alert tint
    "diffEditor.insertedTextBackground": "$glow1/2e",
    "diffEditor.removedTextBackground": "$alert/33",
    "diffEditor.insertedLineBackground": "$glow1/14",
    "diffEditor.removedLineBackground": "$alert/18",
    "diffEditorGutter.insertedLineBackground": "$glow1/26",
    "diffEditorGutter.removedLineBackground": "$alert/2a",
    "diffEditorOverview.insertedForeground": "$glow1/aa",
    "diffEditorOverview.removedForeground": "$alert/aa",
    "diffEditor.border": "$stone",
    "diffEditor.diagonalFill": "$stone/88",
    "diffEditor.unchangedRegionBackground": "$surface",
    "diffEditor.unchangedRegionForeground": "$textSoft",
    "diffEditor.unchangedCodeBackground": "$air4/66",
    "diffEditor.move.border": "$glow3/88",
    "diffEditor.moveActive.border": "$glow3",
    "mergeEditor.change.background": "$glow3/22",
    "merge.currentHeaderBackground": "$glow1/55",
    "merge.currentContentBackground": "$glow1/22",
    "merge.incomingHeaderBackground": "$glow3/55",
    "merge.incomingContentBackground": "$glow3/22",
    "merge.commonHeaderBackground": "$stone2/88",
    "merge.commonContentBackground": "$stone2/44",

    # title bar, menus, command centre
    "titleBar.activeBackground": "$surface",
    "titleBar.activeForeground": "$text",
    "titleBar.inactiveBackground": "$surface",
    "titleBar.inactiveForeground": "$textSoft",
    "titleBar.border": "$stone",
    "window.activeBorder": "$stone",
    "window.inactiveBorder": "$stone",
    "menubar.selectionBackground": "$stone",
    "menubar.selectionForeground": "$hot",
    "menu.background": "$surface",
    "menu.foreground": "$text",
    "menu.selectionBackground": "$stone",
    "menu.selectionForeground": "$hot",
    "menu.separatorBackground": "$stone",
    "menu.border": "$stone",
    "commandCenter.background": "$air1",
    "commandCenter.foreground": "$textSoft",
    "commandCenter.border": "$stone",
    "commandCenter.activeBackground": "$stone",
    "commandCenter.activeForeground": "$hot",
    "commandCenter.activeBorder": "$accent",
    "commandCenter.inactiveBorder": "$stone",

    # activity bar
    "activityBar.background": "$surface",
    "activityBar.foreground": "$accent",
    "activityBar.inactiveForeground": "$textSoft",
    "activityBar.border": "$stone",
    "activityBar.activeBorder": "$accent",
    "activityBar.activeBackground": "$air4",
    "activityBar.activeFocusBorder": "$hot",
    "activityBar.dropBorder": "$accent",
    "activityBarBadge.background": "$accent",
    "activityBarBadge.foreground": "$ink",
    "activityBarTop.foreground": "$accent",
    "activityBarTop.inactiveForeground": "$textSoft",
    "activityBarTop.activeBorder": "$accent",
    "activityBarTop.background": "$surface",

    # side bar
    "sideBar.background": "$surface",
    "sideBar.foreground": "$text",
    "sideBar.border": "$stone",
    "sideBar.dropBackground": "$accent/26",
    "sideBarTitle.foreground": "$hot",
    "sideBarSectionHeader.background": "$air3",
    "sideBarSectionHeader.foreground": "$textSoft",
    "sideBarSectionHeader.border": "$stone",
    "sideBarStickyScroll.background": "$surface",
    "sideBarStickyScroll.border": "$stone",
    "sideBarStickyScroll.shadow": "$none",

    # lists and trees
    "list.activeSelectionBackground": "$stone",
    "list.activeSelectionForeground": "$hot",
    "list.activeSelectionIconForeground": "$hot",
    "list.inactiveSelectionBackground": "$air4",
    "list.inactiveSelectionForeground": "$text",
    "list.hoverBackground": "$air4",
    "list.hoverForeground": "$text",
    "list.focusBackground": "$stone",
    "list.focusForeground": "$hot",
    "list.focusOutline": "$accent",
    "list.focusAndSelectionOutline": "$accent",
    "list.inactiveFocusOutline": "$stone2",
    "list.highlightForeground": "$accent",
    "list.focusHighlightForeground": "$accent",
    "list.dropBackground": "$accent/33",
    "list.errorForeground": "$alert",
    "list.warningForeground": "$hot",
    "list.invalidItemForeground": "$alert",
    "list.deemphasizedForeground": "$textSoft",
    "list.filterMatchBackground": "$hot/30",
    "listFilterWidget.background": "$air4",
    "listFilterWidget.outline": "$accent",
    "listFilterWidget.noMatchesOutline": "$alert",
    "listFilterWidget.shadow": "$none",
    "tree.indentGuidesStroke": "$stone",
    "tree.inactiveIndentGuidesStroke": "$air5",
    "tree.tableColumnsBorder": "$stone",
    "tree.tableOddRowsBackground": "$air3/80",

    # tabs: the active tab carries an accent top border, nothing rounded
    "editorGroupHeader.tabsBackground": "$surface",
    "editorGroupHeader.tabsBorder": "$stone",
    "editorGroupHeader.noTabsBackground": "$surface",
    "editorGroupHeader.border": "$stone",
    "editorGroup.border": "$stone",
    "editorGroup.dropBackground": "$accent/26",
    "editorGroup.emptyBackground": "$bg",
    "editorGroup.focusedEmptyBorder": "$accent",
    "tab.activeBackground": "$bg",
    "tab.activeForeground": "$hot",
    "tab.activeBorder": "$bg",
    "tab.activeBorderTop": "$accent",
    "tab.selectedBackground": "$bg",
    "tab.selectedForeground": "$hot",
    "tab.selectedBorderTop": "$accent",
    "tab.inactiveBackground": "$surface",
    "tab.inactiveForeground": "$textSoft",
    "tab.unfocusedActiveBackground": "$bg",
    "tab.unfocusedActiveForeground": "$text",
    "tab.unfocusedActiveBorder": "$bg",
    "tab.unfocusedActiveBorderTop": "$stone2",
    "tab.unfocusedInactiveBackground": "$surface",
    "tab.unfocusedInactiveForeground": "$textSoft",
    "tab.hoverBackground": "$air4",
    "tab.hoverForeground": "$text",
    "tab.unfocusedHoverBackground": "$air3",
    "tab.border": "$stone",
    "tab.lastPinnedBorder": "$stone2",
    "tab.activeModifiedBorder": "$hot",
    "tab.inactiveModifiedBorder": "$hot/88",
    "tab.unfocusedActiveModifiedBorder": "$hot/88",
    "tab.unfocusedInactiveModifiedBorder": "$hot/55",
    "tab.dragAndDropBorder": "$accent",
    "editorPane.background": "$bg",

    # breadcrumbs
    "breadcrumb.background": "$bg",
    "breadcrumb.foreground": "$textSoft",
    "breadcrumb.focusForeground": "$hot",
    "breadcrumb.activeSelectionForeground": "$hot",
    "breadcrumbPicker.background": "$surface",

    # panel
    "panel.background": "$bg",
    "panel.border": "$stone",
    "panel.dropBorder": "$accent",
    "panelTitle.activeForeground": "$hot",
    "panelTitle.activeBorder": "$accent",
    "panelTitle.inactiveForeground": "$textSoft",
    "panelInput.border": "$stone",
    "panelSection.border": "$stone",
    "panelSectionHeader.background": "$air3",
    "panelSectionHeader.foreground": "$textSoft",
    "panelSectionHeader.border": "$stone",
    "panelStickyScroll.background": "$bg",
    "panelStickyScroll.border": "$stone",
    "panelStickyScroll.shadow": "$none",

    # integrated terminal (the ANSI colours are added from the palette below)
    "terminal.background": "$bg",
    "terminal.foreground": "$text",
    "terminal.selectionBackground": "$stone",
    "terminal.selectionForeground": "$hot",
    "terminal.inactiveSelectionBackground": "$stone/aa",
    "terminal.border": "$stone",
    "terminal.findMatchBackground": "$hot/66",
    "terminal.findMatchBorder": "$hot",
    "terminal.findMatchHighlightBackground": "$hot/30",
    "terminal.hoverHighlightBackground": "$glow3/22",
    "terminal.dropBackground": "$accent/26",
    "terminal.tab.activeBorder": "$accent",
    "terminalCursor.foreground": "$accent",
    "terminalCursor.background": "$bg",
    "terminalCommandDecoration.defaultBackground": "$stone2",
    "terminalCommandDecoration.successBackground": "$glow1",
    "terminalCommandDecoration.errorBackground": "$alert",
    "terminalOverviewRuler.cursorForeground": "$accent",
    "terminalOverviewRuler.findMatchForeground": "$hot",
    "terminalStickyScroll.background": "$bg",
    "terminalStickyScrollHover.background": "$surface",

    # status bar
    "statusBar.background": "$surface",
    "statusBar.foreground": "$textSoft",
    "statusBar.border": "$stone",
    "statusBar.focusBorder": "$accent",
    "statusBar.noFolderBackground": "$surface",
    "statusBar.noFolderForeground": "$textSoft",
    "statusBar.noFolderBorder": "$stone",
    "statusBar.debuggingBackground": "$accent",
    "statusBar.debuggingForeground": "$ink",
    "statusBar.debuggingBorder": "$accent",
    "statusBarItem.hoverBackground": "$stone",
    "statusBarItem.hoverForeground": "$hot",
    "statusBarItem.activeBackground": "$stone2",
    "statusBarItem.focusBorder": "$accent",
    "statusBarItem.prominentBackground": "$air4",
    "statusBarItem.prominentForeground": "$text",
    "statusBarItem.prominentHoverBackground": "$stone",
    "statusBarItem.remoteBackground": "$accent",
    "statusBarItem.remoteForeground": "$ink",
    "statusBarItem.remoteHoverBackground": "$hot",
    "statusBarItem.remoteHoverForeground": "$ink",
    "statusBarItem.errorBackground": "$alert",
    "statusBarItem.errorForeground": "$ink",
    "statusBarItem.errorHoverBackground": "$alert",
    "statusBarItem.errorHoverForeground": "$ink",
    "statusBarItem.warningBackground": "$hot",
    "statusBarItem.warningForeground": "$ink",
    "statusBarItem.warningHoverBackground": "$hot",
    "statusBarItem.warningHoverForeground": "$ink",
    "statusBarItem.offlineBackground": "$alert",
    "statusBarItem.offlineForeground": "$ink",
    "statusBarItem.compactHoverBackground": "$stone2",

    # inputs, dropdowns, checkboxes
    "input.background": "$air1",
    "input.foreground": "$text",
    "input.border": "$stone",
    "input.placeholderForeground": "$stoneLit",
    "inputOption.activeBackground": "$accent/40",
    "inputOption.activeBorder": "$accent",
    "inputOption.activeForeground": "$hot",
    "inputOption.hoverBackground": "$stone",
    "inputValidation.errorBackground": "$surface",
    "inputValidation.errorForeground": "$text",
    "inputValidation.errorBorder": "$alert",
    "inputValidation.warningBackground": "$surface",
    "inputValidation.warningForeground": "$text",
    "inputValidation.warningBorder": "$hot",
    "inputValidation.infoBackground": "$surface",
    "inputValidation.infoForeground": "$text",
    "inputValidation.infoBorder": "$glow3",
    "dropdown.background": "$air1",
    "dropdown.listBackground": "$surface",
    "dropdown.foreground": "$text",
    "dropdown.border": "$stone",
    "checkbox.background": "$air1",
    "checkbox.foreground": "$accent",
    "checkbox.border": "$stone2",
    "checkbox.selectBackground": "$air1",
    "checkbox.selectBorder": "$accent",
    "radio.activeForeground": "$accent",
    "radio.activeBorder": "$accent",
    "radio.inactiveBorder": "$stone2",
    "settings.headerForeground": "$hot",
    "settings.modifiedItemIndicator": "$accent",
    "settings.focusedRowBackground": "$air3",
    "settings.focusedRowBorder": "$stone",
    "settings.rowHoverBackground": "$air3",
    "settings.dropdownBackground": "$air1",
    "settings.dropdownBorder": "$stone",
    "settings.textInputBackground": "$air1",
    "settings.textInputBorder": "$stone",
    "settings.numberInputBackground": "$air1",
    "settings.numberInputBorder": "$stone",
    "settings.checkboxBackground": "$air1",
    "settings.checkboxBorder": "$stone2",
    "settings.checkboxForeground": "$accent",
    "keybindingLabel.background": "$air4",
    "keybindingLabel.foreground": "$text",
    "keybindingLabel.border": "$stone",
    "keybindingLabel.bottomBorder": "$stone2",

    # buttons: accent fill, ink text
    "button.background": "$accent",
    "button.foreground": "$ink",
    "button.hoverBackground": "$hot",
    "button.border": "$none",
    "button.separator": "$ink/66",
    "button.secondaryBackground": "$stone",
    "button.secondaryForeground": "$text",
    "button.secondaryHoverBackground": "$stone2",
    "extensionButton.background": "$accent",
    "extensionButton.foreground": "$ink",
    "extensionButton.hoverBackground": "$hot",
    "extensionButton.separator": "$ink/66",
    "extensionButton.prominentBackground": "$accent",
    "extensionButton.prominentForeground": "$ink",
    "extensionButton.prominentHoverBackground": "$hot",
    "extensionBadge.remoteBackground": "$accent",
    "extensionBadge.remoteForeground": "$ink",
    "extensionIcon.starForeground": "$hot",
    "extensionIcon.verifiedForeground": "$glow3",
    "extensionIcon.preReleaseForeground": "$glow2",

    # scrollbars
    "scrollbar.shadow": "$none",
    "scrollbarSlider.background": "$stone/99",
    "scrollbarSlider.hoverBackground": "$stone2/cc",
    "scrollbarSlider.activeBackground": "$accent/cc",

    # badges and progress
    "badge.background": "$accent",
    "badge.foreground": "$ink",
    "progressBar.background": "$accent",

    # notifications
    "notificationCenter.border": "$stone",
    "notificationCenterHeader.background": "$air4",
    "notificationCenterHeader.foreground": "$hot",
    "notificationToast.border": "$stone",
    "notifications.background": "$surface",
    "notifications.foreground": "$text",
    "notifications.border": "$stone",
    "notificationLink.foreground": "$glow3",
    "notificationsErrorIcon.foreground": "$alert",
    "notificationsWarningIcon.foreground": "$hot",
    "notificationsInfoIcon.foreground": "$glow3",

    # quick input (command palette)
    "quickInput.background": "$surface",
    "quickInput.foreground": "$text",
    "quickInputTitle.background": "$air4",
    "quickInputList.focusBackground": "$stone",
    "quickInputList.focusForeground": "$hot",
    "quickInputList.focusIconForeground": "$hot",
    "pickerGroup.border": "$stone",
    "pickerGroup.foreground": "$accent",

    # git decorations
    "gitDecoration.addedResourceForeground": "$glow1",
    "gitDecoration.untrackedResourceForeground": "$glow1",
    "gitDecoration.modifiedResourceForeground": "$hot",
    "gitDecoration.stageModifiedResourceForeground": "$hot",
    "gitDecoration.deletedResourceForeground": "$alert",
    "gitDecoration.stageDeletedResourceForeground": "$alert",
    "gitDecoration.renamedResourceForeground": "$glow3",
    "gitDecoration.conflictingResourceForeground": "$glow2",
    "gitDecoration.ignoredResourceForeground": "$stoneLit",
    "gitDecoration.submoduleResourceForeground": "$typeSoft",
    "scmGraph.historyItemRefColor": "$accent",
    "scmGraph.historyItemRemoteRefColor": "$glow2",
    "scmGraph.historyItemBaseRefColor": "$glow3",
    "scmGraph.foreground1": "$accent",
    "scmGraph.foreground2": "$glow3",
    "scmGraph.foreground3": "$glow2",
    "scmGraph.foreground4": "$glow1",
    "scmGraph.foreground5": "$hot",

    # debug, testing, problems
    "debugToolBar.background": "$surface",
    "debugToolBar.border": "$stone",
    "debugIcon.breakpointForeground": "$alert",
    "debugIcon.breakpointDisabledForeground": "$stone2",
    "debugIcon.breakpointUnverifiedForeground": "$stoneLit",
    "debugIcon.startForeground": "$glow1",
    "debugIcon.pauseForeground": "$hot",
    "debugIcon.stopForeground": "$alert",
    "debugIcon.restartForeground": "$glow1",
    "debugIcon.continueForeground": "$glow3",
    "debugIcon.stepOverForeground": "$glow3",
    "debugIcon.stepIntoForeground": "$glow3",
    "debugIcon.stepOutForeground": "$glow3",
    "debugIcon.disconnectForeground": "$alert",
    "debugTokenExpression.name": "$property",
    "debugTokenExpression.value": "$textSoft",
    "debugTokenExpression.string": "$string",
    "debugTokenExpression.number": "$glow1",
    "debugTokenExpression.boolean": "$glow1",
    "debugTokenExpression.error": "$alert",
    "debugConsole.errorForeground": "$alert",
    "debugConsole.warningForeground": "$hot",
    "debugConsole.infoForeground": "$glow3",
    "debugConsole.sourceForeground": "$textSoft",
    "debugConsoleInputIcon.foreground": "$accent",
    "testing.iconPassed": "$glow1",
    "testing.iconFailed": "$alert",
    "testing.iconErrored": "$alert",
    "testing.iconQueued": "$hot",
    "testing.iconUnset": "$stoneLit",
    "testing.iconSkipped": "$textSoft",
    "testing.runAction": "$glow1",
    "problemsErrorIcon.foreground": "$alert",
    "problemsWarningIcon.foreground": "$hot",
    "problemsInfoIcon.foreground": "$glow3",

    # welcome page, walkthroughs, charts
    "welcomePage.background": "$bg",
    "welcomePage.tileBackground": "$surface",
    "welcomePage.tileHoverBackground": "$air4",
    "welcomePage.tileBorder": "$stone",
    "welcomePage.progress.background": "$air4",
    "welcomePage.progress.foreground": "$accent",
    "walkThrough.embeddedEditorBackground": "$air1",
    "charts.foreground": "$text",
    "charts.lines": "$stone2",
    "charts.red": "$alert",
    "charts.green": "$glow1",
    "charts.yellow": "$hot",
    "charts.blue": "$glow3",
    "charts.orange": "$accent",
    "charts.purple": "$type",

    # symbol icons (outline, suggest, breadcrumbs)
    "symbolIcon.classForeground": "$type",
    "symbolIcon.structForeground": "$type",
    "symbolIcon.enumeratorForeground": "$type",
    "symbolIcon.interfaceForeground": "$typeSoft",
    "symbolIcon.typeParameterForeground": "$typeSoft",
    "symbolIcon.functionForeground": "$glow3",
    "symbolIcon.methodForeground": "$glow3",
    "symbolIcon.constructorForeground": "$glow3",
    "symbolIcon.variableForeground": "$text",
    "symbolIcon.fieldForeground": "$property",
    "symbolIcon.propertyForeground": "$property",
    "symbolIcon.constantForeground": "$glow1",
    "symbolIcon.enumeratorMemberForeground": "$glow1",
    "symbolIcon.numberForeground": "$glow1",
    "symbolIcon.booleanForeground": "$glow1",
    "symbolIcon.stringForeground": "$string",
    "symbolIcon.keywordForeground": "$hot",
    "symbolIcon.namespaceForeground": "$typeSoft",
    "symbolIcon.moduleForeground": "$typeSoft",
    "symbolIcon.packageForeground": "$typeSoft",
    "symbolIcon.fileForeground": "$textSoft",
    "symbolIcon.folderForeground": "$textSoft",
}

TERMINAL_KEYS = {
    "black": "ansiBlack", "red": "ansiRed", "green": "ansiGreen", "yellow": "ansiYellow",
    "blue": "ansiBlue", "magenta": "ansiMagenta", "cyan": "ansiCyan", "white": "ansiWhite",
    "brightBlack": "ansiBrightBlack", "brightRed": "ansiBrightRed",
    "brightGreen": "ansiBrightGreen", "brightYellow": "ansiBrightYellow",
    "brightBlue": "ansiBrightBlue", "brightMagenta": "ansiBrightMagenta",
    "brightCyan": "ansiBrightCyan", "brightWhite": "ansiBrightWhite",
}


def rule(name, scopes, fg=None, style=None):
    settings = {}
    if fg is not None:
        settings["foreground"] = fg
    if style is not None:
        settings["fontStyle"] = style
    return {"name": name, "scope": scopes, "settings": settings}


TOKENS = [
    rule("Comments", [
        "comment", "punctuation.definition.comment", "string.comment",
    ], "$comment", "italic"),
    rule("Doc comment tags", [
        "comment.block.documentation storage.type.class", "comment keyword.other.documentation",
        "storage.type.class.doxygen", "comment.block.documentation entity.name.type",
        "keyword.other.documentation.rust",
    ], "$textSoft", "italic"),

    rule("Variables and plain text", [
        "variable", "variable.other", "variable.other.readwrite", "meta.definition.variable",
        "source", "support.variable", "string.unquoted.argument.shell",
    ], "$text"),
    rule("Parameters", [
        "variable.parameter", "meta.function.parameters variable.other",
        "variable.parameter.function.language.python", "variable.parameter.name.nix",
        "variable.parameter.function.nix", "variable.parameter.function.4.nix",
    ], "$text", "italic"),
    rule("Language variables (this, self, super)", [
        "variable.language", "variable.language.this", "variable.language.self.rust",
        "variable.parameter.function.language.special", "variable.language.special.self.python",
        "variable.language.special.cls.python", "keyword.other.this",
    ], "$hot", "italic"),
    rule("Members and properties", [
        "variable.other.member", "variable.other.property", "variable.other.object.property",
        "meta.object-literal.key", "support.type.property-name", "meta.attribute.python",
        "entity.name.variable.field",
    ], "$property"),

    rule("Keywords", [
        "keyword", "keyword.control", "keyword.other", "storage", "storage.type", "storage.modifier",
        "keyword.operator.new", "keyword.operator.delete", "keyword.operator.sizeof",
        "keyword.operator.alignof", "keyword.operator.typeid", "keyword.operator.cast",
        "keyword.operator.expression", "keyword.operator.logical.python",
        "keyword.operator.wordlike", "keyword.operator.noexcept", "keyword.operator.word",
        "storage.type.function.python", "storage.type.class.python", "keyword.other.fn.rust",
        "storage.type.rust", "storage.modifier.mut.rust", "keyword.other.crate.rust",
        "keyword.other.nix", "keyword.other.inherit.nix", "keyword.control.shell",
        "storage.type.struct", "storage.type.enum", "storage.type.class", "storage.type.union",
        "storage.type.namespace", "storage.type.template", "storage.modifier.specifier",
    ], "$hot"),
    rule("Operators and punctuation", [
        "keyword.operator", "punctuation", "punctuation.separator", "punctuation.terminator",
        "punctuation.accessor", "meta.brace", "punctuation.section", "punctuation.definition.block",
        "keyword.operator.assignment", "keyword.operator.arithmetic", "keyword.operator.comparison",
        "keyword.operator.logical", "keyword.operator.nix", "keyword.operator.pipe.shell",
        "keyword.operator.redirect.shell", "keyword.operator.list.shell",
        "punctuation.definition.parameters", "punctuation.definition.arguments",
        "punctuation.definition.typeparameters", "punctuation.definition.attribute-selector",
    ], "$textSoft"),
    rule("Preprocessor and directives", [
        "meta.preprocessor", "keyword.control.directive", "keyword.control.import",
        "punctuation.definition.directive", "keyword.other.directive", "keyword.control.at-rule",
        "meta.preprocessor.macro", "keyword.control.directive.include",
        "keyword.control.directive.define", "keyword.control.directive.conditional",
    ], "$accent"),
    rule("Macro names", [
        "entity.name.function.preprocessor", "entity.name.function.macro",
        "support.function.macro", "entity.name.function.macro.rust", "support.macro.rust",
        "meta.preprocessor.macro entity.name.function",
    ], "$typeSoft"),

    rule("Numbers and constants", [
        "constant", "constant.numeric", "constant.language", "constant.character",
        "constant.other", "variable.other.constant", "support.constant",
        "keyword.other.unit", "constant.language.boolean", "constant.language.null",
        "constant.language.nullptr", "constant.language.python", "constant.language.nix",
        "constant.numeric.nix", "constant.language.bool.rust", "constant.numeric.decimal.rust",
        "variable.other.enummember", "constant.other.caps", "entity.name.constant",
        "constant.other.color",
    ], "$glow1"),
    rule("Strings", [
        "string", "string.quoted", "string.template", "punctuation.definition.string",
        "string.quoted.double.nix", "string.quoted.other.nix", "string.interpolated",
        "string.unquoted.heredoc", "string.quoted.docstring", "string.quoted.double.include",
        "string.quoted.other.lt-gt.include", "string.quoted.single.shell",
        "string.quoted.double.shell", "meta.embedded.assembly",
    ], "$string"),
    rule("Paths and URLs", [
        "string.unquoted.path.nix", "string.unquoted.spath.nix", "string.unquoted.url.nix",
        "constant.other.path", "string.other.link", "markup.underline.link",
        "meta.link.inline.markdown markup.underline.link", "string.regexp",
    ], "$glow3"),
    rule("Escapes, format placeholders and interpolation marks", [
        "constant.character.escape", "constant.other.placeholder", "constant.character.format",
        "punctuation.section.embedded", "punctuation.definition.template-expression",
        "punctuation.definition.interpolation", "meta.interpolation punctuation",
        "punctuation.section.interpolation", "constant.character.format.placeholder",
        "punctuation.definition.variable.shell", "keyword.operator.expansion.shell",
        "punctuation.section.embedded.begin.nix", "punctuation.section.embedded.end.nix",
    ], "$hot"),
    rule("Interpolated code is code again", [
        "meta.embedded", "meta.interpolation", "meta.template.expression",
        "meta.embedded.line", "source.nix meta.embedded",
    ], "$text"),

    rule("Functions and methods", [
        "entity.name.function", "support.function", "meta.function-call entity.name.function",
        "meta.function-call.generic", "entity.name.function.call", "entity.name.function.member",
        "entity.name.function.definition", "support.function.builtin", "entity.name.method",
        "meta.method-call entity.name.function", "entity.name.function.rust",
        "support.function.builtin.nix", "entity.name.function.nix", "support.function.magic.python",
        "entity.name.command", "entity.name.function.shell",
        "support.function.builtin.shell", "entity.name.command.shell", "variable.function",
        "entity.name.operator",
    ], "$glow3"),
    rule("Types, classes, structs, enums", [
        "entity.name.type", "entity.name.class", "entity.name.struct", "entity.name.enum",
        "entity.name.union", "support.class", "support.type", "entity.other.inherited-class",
        "entity.name.type.class", "entity.name.type.struct", "entity.name.type.enum",
        "entity.name.type.alias", "entity.name.type.rust", "support.type.python",
        "meta.type.annotation entity.name", "entity.name.type.template",
        "entity.name.type.class.templated", "support.type.exception.python",
    ], "$type"),
    rule("Built-in types, traits, interfaces, namespaces, type parameters", [
        "storage.type.built-in", "storage.type.primitive", "support.type.primitive",
        "support.type.builtin", "keyword.other.type", "storage.type.built-in.primitive",
        "entity.name.type.numeric.rust", "entity.name.type.primitive.rust",
        "entity.name.type.interface", "entity.name.type.trait", "entity.name.namespace",
        "entity.name.scope-resolution", "entity.name.type.namespace", "entity.name.module",
        "entity.name.type.parameter", "entity.name.type.module", "storage.type.cs",
        "support.type.posix-reserved", "storage.type.integral", "storage.type.floating",
        "storage.type.language", "entity.name.lifetime.rust", "punctuation.definition.lifetime.rust",
    ], "$typeSoft"),
    rule("Decorators, attributes, annotations", [
        "meta.decorator", "punctuation.decorator", "entity.name.function.decorator.python",
        "meta.attribute.rust", "punctuation.definition.attribute", "meta.annotation",
        "storage.type.annotation", "punctuation.definition.annotation",
        "support.other.attribute", "entity.other.attribute.cpp",
    ], "$typeSoft", "italic"),

    rule("Tags", ["entity.name.tag", "punctuation.definition.tag"], "$hot"),
    rule("Attribute names", [
        "entity.other.attribute-name", "entity.other.attribute-name.multipart.nix",
        "entity.other.attribute-name.single.nix", "variable.other.assignment.shell",
        "variable.other.normal.shell", "variable.other.special.shell",
        "variable.other.positional.shell", "variable.other.bracket.shell",
    ], "$property"),

    rule("JSON, YAML and TOML keys", [
        "support.type.property-name.json", "string.json support.type.property-name",
        "entity.name.tag.yaml", "support.type.property-name.toml",
        "entity.name.tag.toml", "support.type.property-name.table.toml",
        "punctuation.support.type.property-name",
    ], "$glow3"),
    rule("Markdown headings", [
        "markup.heading", "entity.name.section", "punctuation.definition.heading",
        "markup.heading.setext",
    ], "$hot", "bold"),
    rule("Markdown bold", ["markup.bold", "punctuation.definition.bold"], "$accent", "bold"),
    rule("Markdown italic", ["markup.italic", "punctuation.definition.italic"], "$typeSoft", "italic"),
    rule("Markdown strikethrough", ["markup.strikethrough"], "$textSoft", "strikethrough"),
    rule("Markdown inline and fenced code", [
        "markup.inline.raw", "markup.fenced_code.block", "markup.raw.block",
        "punctuation.definition.raw", "fenced_code.block.language",
    ], "$glow1"),
    rule("Markdown quotes", ["markup.quote", "punctuation.definition.quote"], "$comment", "italic"),
    rule("Markdown lists and rules", [
        "punctuation.definition.list", "beginning.punctuation.definition.list",
        "meta.separator.markdown",
    ], "$accent"),
    rule("Markdown link text", [
        "string.other.link.title", "string.other.link.description", "meta.link.reference",
        "constant.other.reference.link",
    ], "$glow3"),

    rule("Diff: added", ["markup.inserted", "punctuation.definition.inserted"], "$glow1"),
    rule("Diff: removed", ["markup.deleted", "punctuation.definition.deleted"], "$alert"),
    rule("Diff: changed", ["markup.changed", "punctuation.definition.changed"], "$hot"),
    rule("Diff: headers", ["meta.diff", "meta.diff.header", "meta.diff.range"], "$glow3"),

    rule("Invalid and deprecated", ["invalid", "invalid.illegal"], "$alert"),
    rule("Deprecated", ["invalid.deprecated"], "$alert", "strikethrough"),

    rule("Token info", ["token.info-token"], "$glow3"),
    rule("Token warn", ["token.warn-token"], "$hot"),
    rule("Token error", ["token.error-token"], "$alert"),
    rule("Token debug", ["token.debug-token"], "$type"),
]

SEMANTIC = {
    "comment": {"foreground": "$comment", "italic": True},
    "keyword": "$hot",
    "number": "$glow1",
    "boolean": "$glow1",
    "string": "$string",
    "regexp": "$glow3",
    "operator": "$textSoft",
    "variable": "$text",
    "variable.constant": "$glow1",
    "variable.defaultLibrary": "$typeSoft",
    "variable.global": "$text",
    "parameter": {"foreground": "$text", "italic": True},
    "property": "$property",
    "enumMember": "$glow1",
    "const": "$glow1",
    "constant": "$glow1",
    "function": "$glow3",
    "method": "$glow3",
    "function.defaultLibrary": "$glow3",
    "macro": "$typeSoft",
    "decorator": {"foreground": "$typeSoft", "italic": True},
    "attribute": {"foreground": "$typeSoft", "italic": True},
    "type": "$type",
    "class": "$type",
    "struct": "$type",
    "enum": "$type",
    "union": "$type",
    "typeAlias": "$type",
    "type.defaultLibrary": "$typeSoft",
    "builtinType": "$typeSoft",
    "interface": "$typeSoft",
    "trait": "$typeSoft",
    "typeParameter": "$typeSoft",
    "templateParameter": "$typeSoft",
    "concept": "$typeSoft",
    "namespace": "$typeSoft",
    "module": "$typeSoft",
    "lifetime": {"foreground": "$typeSoft", "italic": True},
    "selfKeyword": {"foreground": "$hot", "italic": True},
    "selfTypeKeyword": "$typeSoft",
    "label": "$accent",
    "formatSpecifier": "$hot",
    "escapeSequence": "$hot",
    "unresolvedReference": "$alert",
    "*.deprecated": {"strikethrough": True},
}

HEX = re.compile(r"^#(?:[0-9a-f]{6}|[0-9a-f]{8})$")
REF = re.compile(r"^\$([A-Za-z0-9]+)(?:/([0-9a-f]{2}))?$")


def resolve(value, pal):
    """Turn "$name" or "$name/AA" into a hex colour; pass anything else through."""
    if isinstance(value, dict):
        return {k: resolve(v, pal) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, pal) for v in value]
    if not isinstance(value, str) or not value.startswith("$"):
        return value
    m = REF.match(value)
    if not m:
        raise SystemExit(f"bad colour reference: {value!r}")
    name, alpha = m.groups()
    if name not in pal:
        raise SystemExit(f"unknown palette key: {name!r}")
    colour = pal[name]
    if alpha:
        if len(colour) != 7:
            raise SystemExit(f"cannot add alpha to {name!r} ({colour})")
        colour += alpha
    return colour


def build(key):
    spec = THEMES[key]
    pal = dict(WORLD)
    pal.update({k: v for k, v in spec.items() if isinstance(v, str) and v.startswith("#")})
    colors = resolve(COLORS, pal)
    for name, vs in TERMINAL_KEYS.items():
        colors["terminal." + vs] = spec["term"][name]
    return {
        "$schema": "vscode://schemas/color-theme",
        "name": spec["label"],
        "type": "dark",
        "semanticHighlighting": True,
        "colors": colors,
        "tokenColors": [
            {"name": r["name"], "scope": r["scope"], "settings": resolve(r["settings"], pal)}
            for r in TOKENS
        ],
        "semanticTokenColors": resolve(SEMANTIC, pal),
    }, pal


# ---- validation and contrast ------------------------------------------------------------

def luminance(hex6):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a[:7]), luminance(b[:7])), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def colours_in(theme):
    """Yield (where, colour) for every colour value in a theme."""
    for k, v in theme["colors"].items():
        yield f"colors.{k}", v
    for r in theme["tokenColors"]:
        if "foreground" in r["settings"]:
            yield f"tokenColors[{r['name']}]", r["settings"]["foreground"]
    for k, v in theme["semanticTokenColors"].items():
        if isinstance(v, str):
            yield f"semanticTokenColors.{k}", v
        elif "foreground" in v:
            yield f"semanticTokenColors.{k}", v["foreground"]


# (label, palette key, minimum ratio against the editor background)
CHECKS = [
    ("body text (editor.foreground)", "text", 7.0),
    ("keywords (accent-hot)", "hot", 4.5),
    ("numbers, constants (glow-1)", "glow1", 4.5),
    ("strings", "string", 4.5),
    ("functions (glow-3)", "glow3", 4.5),
    ("types", "type", 4.5),
    ("built-in types, namespaces", "typeSoft", 4.5),
    ("comments (muted violet)", "comment", 4.5),
    ("properties, attribute names", "property", 4.5),
    ("operators, punctuation (text-soft)", "textSoft", 4.5),
    ("preprocessor, cursor (accent)", "accent", 4.5),
    ("errors (alert)", "alert", 4.5),
]


def check(key, theme, pal):
    problems = []
    for where, colour in colours_in(theme):
        if not isinstance(colour, str) or not HEX.match(colour):
            problems.append(f"{key}: {where} is not a hex colour: {colour!r}")
    bg = theme["colors"]["editor.background"]
    rows = []
    for label, name, minimum in CHECKS:
        ratio = contrast(pal[name], bg)
        rows.append((label, pal[name], ratio, minimum))
        if ratio < minimum:
            problems.append(f"{key}: {label} {pal[name]} is {ratio:.2f}:1, needs {minimum}:1")
    # every syntax colour actually used, not only the named ones above
    for where, colour in colours_in(theme):
        if where.startswith("colors."):
            continue
        ratio = contrast(colour, bg)
        if ratio < 4.5:
            problems.append(f"{key}: {where} {colour} is {ratio:.2f}:1 on {bg}")
    # ink on the accent fill (buttons, badges)
    for fill in ("button.background", "button.hoverBackground", "badge.background"):
        ratio = contrast(theme["colors"]["button.foreground"], theme["colors"][fill])
        rows.append((f"ink on {fill}", theme["colors"][fill], ratio, 4.5))
        if ratio < 4.5:
            problems.append(f"{key}: ink on {fill} is {ratio:.2f}:1")
    return rows, problems


def main():
    write = "--check" not in sys.argv[1:]
    out = HERE / "themes"
    problems = []
    tables = {}
    for key in THEMES:
        theme, pal = build(key)
        path = out / f"glowgrid-{key}-color-theme.json"
        text = json.dumps(theme, indent=2) + "\n"
        if write:
            out.mkdir(exist_ok=True)
            path.write_text(text)
        elif not path.exists() or path.read_text() != text:
            problems.append(f"{key}: {path.name} is missing or differs from the template; run generate.py")
        if path.exists():
            theme = json.loads(path.read_text())  # check what is on disk
        tables[key], p = check(key, theme, pal)
        problems += p

    # package.json must list exactly these files as dark themes
    pkg = json.loads((HERE / "package.json").read_text())
    listed = {t["path"]: t for t in pkg["contributes"]["themes"]}
    for key, spec in THEMES.items():
        entry = listed.get(f"./themes/glowgrid-{key}-color-theme.json")
        if not entry:
            problems.append(f"package.json does not list the {key} theme")
        elif entry.get("label") != spec["label"] or entry.get("uiTheme") != "vs-dark":
            problems.append(f"package.json entry for {key} has the wrong label or uiTheme")
    if len(listed) != len(THEMES):
        problems.append("package.json lists themes the generator does not produce")

    for key, rows in tables.items():
        print(f"\n{THEMES[key]['label']}  (on #0b0714)")
        for label, colour, ratio, minimum in rows:
            flag = "ok" if ratio >= minimum else "FAIL"
            print(f"  {label:38s} {colour:9s} {ratio:5.2f}:1  (min {minimum}) {flag}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\nall checks passed" + (" (files written)" if write else " (files on disk match the template)"))


if __name__ == "__main__":
    main()
