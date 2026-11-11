// Glowgrid for VS Code. The colour themes need no code; this file is for the look-and-feel
// commands, which add ui.css to VS Code's own workbench stylesheet.
//
// VS Code has no supported way for an extension to restyle its window, so this edits a file
// in the VS Code installation and updates the checksum VS Code keeps for it. That means:
//   - it has to be re-applied after each VS Code update (the extension offers to);
//   - it cannot work when VS Code is installed read-only (Nix, Snap, some system packages).
//     On NixOS the same ui.css is applied when the package is built instead; see the README.
"use strict";
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const START = "/* glowgrid-ui:start */";
const END = "/* glowgrid-ui:end */";
const CSS_KEY = "vs/workbench/workbench.desktop.main.css";
const BLOCKS = { corners: "squareCorners", shadows: "hardShadows", font: "interfaceFont", labels: "pixelLabels", motion: "steppedMotion" };

function paths() {
  const root = vscode.env.appRoot;
  return { css: path.join(root, "out", ...CSS_KEY.split("/")), product: path.join(root, "product.json") };
}

/** ui.css with the blocks the user switched off removed. */
function buildCss(context) {
  const cfg = vscode.workspace.getConfiguration("glowgrid.ui");
  const raw = fs.readFileSync(path.join(context.extensionPath, "ui.css"), "utf8");
  return raw.replace(/\/\*@(\w+)\*\/([\s\S]*?)\/\*@end\*\//g, (_, name, body) => (cfg.get(BLOCKS[name], true) ? body : ""));
}

function strip(text) {
  const a = text.indexOf(START), b = text.indexOf(END);
  return a >= 0 && b > a ? text.slice(0, a).replace(/\n+$/, "\n") + text.slice(b + END.length).replace(/^\n+/, "") : text;
}

/** VS Code's own checksum: SHA-256, base64, without padding. */
function checksum(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("base64").replace(/=+$/, "");
}

function updateChecksum(p) {
  try {
    const product = JSON.parse(fs.readFileSync(p.product, "utf8"));
    if (product.checksums && product.checksums[CSS_KEY]) {
      product.checksums[CSS_KEY] = checksum(p.css);
      fs.writeFileSync(p.product, JSON.stringify(product, null, "\t"));
    }
  } catch (e) {
    // Not fatal: VS Code then shows its "installation appears to be corrupt" notice, which can be dismissed.
  }
}

function isApplied() {
  try { return fs.readFileSync(paths().css, "utf8").includes(START); } catch (e) { return false; }
}

function explain(e) {
  if (e && (e.code === "EROFS" || e.code === "EACCES" || e.code === "EPERM")) {
    return "VS Code's files cannot be changed here (" + e.code + "). It is installed read-only or owned by another user. " +
      "On NixOS, apply the style when the package is built (see the Glowgrid README). On other systems, run VS Code once with write access to its installation folder.";
  }
  return "Glowgrid could not change VS Code's stylesheet: " + (e && e.message ? e.message : String(e));
}

async function write(context, on) {
  const p = paths();
  try {
    const current = fs.readFileSync(p.css, "utf8");
    const clean = strip(current);
    const next = on ? clean.replace(/\n*$/, "\n") + START + "\n" + buildCss(context) + "\n" + END + "\n" : clean;
    if (next === current) {
      vscode.window.showInformationMessage(on ? "Glowgrid UI style is already applied." : "Glowgrid UI style is not applied.");
      return;
    }
    fs.writeFileSync(p.css, next);
    updateChecksum(p);
    await context.globalState.update("glowgrid.appliedTo", on ? vscode.version : undefined);
    const pick = await vscode.window.showInformationMessage(
      on ? "Glowgrid UI style applied. Restart VS Code to see it." : "Glowgrid UI style removed. Restart VS Code to finish.", "Restart now");
    if (pick) vscode.commands.executeCommand("workbench.action.reloadWindow");
  } catch (e) {
    vscode.window.showErrorMessage(explain(e));
  }
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("glowgrid.applyUi", () => write(context, true)),
    vscode.commands.registerCommand("glowgrid.removeUi", () => write(context, false)),
    vscode.commands.registerCommand("glowgrid.uiStatus", () => {
      vscode.window.showInformationMessage(isApplied()
        ? "Glowgrid UI style is applied to this VS Code installation."
        : "Glowgrid UI style is not applied. Run \"Glowgrid: Apply UI Style\".");
    }),
    // changing a glowgrid.ui.* setting only matters if the style is the extension's to manage
    vscode.workspace.onDidChangeConfiguration(async e => {
      if (!e.affectsConfiguration("glowgrid.ui") || !context.globalState.get("glowgrid.appliedTo")) return;
      const pick = await vscode.window.showInformationMessage("Glowgrid UI settings changed. Apply them now?", "Apply");
      if (pick) write(context, true);
    })
  );
  // a VS Code update replaces the stylesheet: offer to put the style back, once per version
  const applied = context.globalState.get("glowgrid.appliedTo");
  if (applied && applied !== vscode.version && !isApplied()) {
    vscode.window.showInformationMessage("VS Code was updated and the Glowgrid UI style was removed with it. Apply it again?", "Apply")
      .then(pick => { if (pick) write(context, true); else context.globalState.update("glowgrid.appliedTo", undefined); });
  }
}

module.exports = { activate, deactivate() {}, _test: { strip, START, END } };
