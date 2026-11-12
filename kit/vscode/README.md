# Glowgrid for VS Code

Colour themes and the look and feel around them, in the
[Glowgrid](https://github.com/maxmaster55/pixal_design_system) pixel style.

## What it does

1. **Colour themes**: Glowgrid Ember, Forge, Frost and Geode. Ember becomes the default theme when
   the extension is installed; change it with `Ctrl+K Ctrl+T`.
2. **Follows the desktop.** On a Glowgrid desktop, running `glowgrid-theme forge` (or ember,
   frost, geode) switches VS Code's colour theme too, in every open window. It reads
   `~/.local/state/glowgrid/theme`. Turn it off with `glowgrid.followDesktopTheme`; it also
   stays out of the way if you pick a non-Glowgrid colour theme.
3. **Defaults** for things a theme cannot set: a block cursor that blinks instead of fading,
   no smooth scrolling or smooth caret, square selections, no ligatures, and VT323 in the
   integrated terminal. These are defaults only; anything you set yourself wins.
4. **UI style** (`ui.css`): square corners everywhere, hard offset shadows on menus and
   popups, IBM Plex Sans for the interface, Silkscreen section titles, VT323 in the status
   bar, and stepped hover changes.

## Applying the UI style

VS Code gives extensions no supported way to restyle its window, so the style is added to
VS Code's own stylesheet. There are two ways.

**Ordinary installations** (a .deb, .rpm, tarball or Windows/macOS install you can write to):
run **Glowgrid: Apply UI Style** from the command palette, then restart. Run
**Glowgrid: Remove UI Style** to undo it. A VS Code update removes the style; the extension
offers to put it back.

**Read-only installations** (NixOS, Snap): the command cannot write there and says so. On
NixOS, append `ui.css` when the package is built:

```nix
pkgs.vscode.overrideAttrs (old: {
  nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.jq pkgs.openssl ];
  postFixup = (old.postFixup or "") + ''
    app=$out/lib/vscode/resources/app
    css=$app/out/vs/workbench/workbench.desktop.main.css
    { echo '/* glowgrid-ui:start */'; sed -e 's#/\*@[a-z]*\*/##g' ${./ui.css}; echo '/* glowgrid-ui:end */'; } >> "$css"
    sum=$(openssl dgst -sha256 -binary "$css" | base64 | tr -d '=')
    jq --arg s "$sum" '.checksums["vs/workbench/workbench.desktop.main.css"] = $s' "$app/product.json" > p.json && mv p.json "$app/product.json"
  '';
})
```

The last two lines update the checksum VS Code keeps for that file, so it does not warn
that the installation is corrupt.

## Settings

Each part of the UI style can be switched off (ordinary installations; re-apply after changing):

| Setting | Default | Controls |
| --- | --- | --- |
| `glowgrid.ui.squareCorners` | on | Square corners |
| `glowgrid.ui.hardShadows` | on | Hard offset shadows on floating things |
| `glowgrid.ui.interfaceFont` | on | IBM Plex Sans for the interface |
| `glowgrid.ui.pixelLabels` | on | Silkscreen titles, VT323 status bar and badges |
| `glowgrid.ui.steppedMotion` | on | Hover and selection change in two steps |

To change the style itself, edit `ui.css`: each block sits between `/*@name*/` and `/*@end*/`.

## Fonts

Install Pixelify Sans, Silkscreen, VT323 and IBM Plex Sans (all free, on Google Fonts and in
the design system's `fonts/` folder). Without them VS Code falls back to its usual fonts.

## Regenerating the themes

`python3 generate.py` rewrites the four theme files from one template and checks contrast.
