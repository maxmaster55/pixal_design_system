FIELD BOOK FONTS
================
These are the four typefaces used in the Ember Cave field books
(Reverse Engineering, Rust Forge, NixOS Frost). None were generated:
they are existing open-source fonts from Google Fonts.

  Role in the books            Font            Folder
  ---------------------------  --------------  -------------
  Titles, part/chapter heads   Pixelify Sans   PixelifySans/
  Small labels, tags, page no. Silkscreen      Silkscreen/
  Code blocks, terminal text   VT323           VT323/
  Body text                    IBM Plex Sans   IBMPlexSans/

INSTALL
  Windows: select the .ttf files > right-click > Install (or "Install for all users").
  macOS:   double-click each .ttf > Install Font (Font Book).
  Linux:   copy to ~/.local/share/fonts/ then run: fc-cache -f

  Install the static .ttf files in each folder. The variable/ subfolders hold
  the original variable fonts (all weights in one file) for apps that support
  them; don't install both versions of the same family at once.

LICENSE
  All four fonts are licensed under the SIL Open Font License 1.1 (OFL.txt in
  each folder): free to use in personal and commercial work, embed in PDFs and
  bundle; you may not sell the fonts by themselves.
  Sources: github.com/google/fonts (ofl/pixelifysans, ofl/silkscreen, ofl/vt323,
  ofl/ibmplexsans). Static weights were cut from the official variable fonts
  with fontTools; the outlines are unchanged.
