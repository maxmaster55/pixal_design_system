-- Glowgrid for Neovim: a dark world lit from within. Ember, Forge and Frost.
--   :colorscheme glowgrid
-- The theme follows the desktop's (~/.local/state/glowgrid/theme) when that file exists;
-- otherwise set vim.g.glowgrid_theme = "ember" | "forge" | "frost" before loading.
vim.cmd("highlight clear")
if vim.fn.exists("syntax_on") == 1 then vim.cmd("syntax reset") end
vim.o.background = "dark"
vim.o.termguicolors = true
vim.g.colors_name = "glowgrid"

local themes = {
  ember = { accent = "#ff8a2a", hot = "#ffd36b", glow1 = "#7cf36b", glow2 = "#e94bd6", glow3 = "#4bc6e9", string = "#ffa565", type = "#f06fe0" },
  forge = { accent = "#ff9a3c", hot = "#ffc56a", glow1 = "#ffe08a", glow2 = "#f07a22", glow3 = "#bdf0ff", string = "#b4e06b", type = "#f07a22" },
  frost = { accent = "#4bc6e9", hot = "#bdf0ff", glow1 = "#8fe3f7", glow2 = "#e6fbff", glow3 = "#ffd36b", string = "#ffb38f", type = "#b9a4ff" },
}

local function current()
  local path = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/glowgrid/theme"
  local f = io.open(path, "r")
  if f then
    local name = (f:read("*l") or ""):gsub("%s+", "")
    f:close()
    if themes[name] then return name end
  end
  return themes[vim.g.glowgrid_theme] and vim.g.glowgrid_theme or "ember"
end

local t = themes[current()]
-- the dark world, shared by every theme
local bg, surface, air3, air5, stone, stone_lit = "#0b0714", "#170d24", "#1b1029", "#2f1a44", "#3b2a3f", "#8a5a5a"
local text, soft, ink, alert, comment, prop = "#e9def0", "#a493b0", "#1c1226", "#ff5f5f", "#9482ad", "#cfc0e6"

local function hi(group, spec) vim.api.nvim_set_hl(0, group, spec) end

-- editor
hi("Normal", { fg = text, bg = bg })
hi("NormalNC", { fg = text, bg = bg })
hi("NormalFloat", { fg = text, bg = surface })
hi("FloatBorder", { fg = t.accent, bg = surface })
hi("FloatTitle", { fg = t.hot, bg = surface, bold = true })
hi("Cursor", { fg = bg, bg = t.accent })
hi("CursorLine", { bg = surface })
hi("CursorColumn", { bg = surface })
hi("ColorColumn", { bg = surface })
hi("LineNr", { fg = stone_lit })
hi("CursorLineNr", { fg = t.hot, bold = true })
hi("SignColumn", { bg = bg })
hi("FoldColumn", { fg = stone_lit, bg = bg })
hi("Folded", { fg = soft, bg = air3 })
hi("VertSplit", { fg = "#000000", bg = bg })
hi("WinSeparator", { fg = stone, bg = bg })
hi("Visual", { bg = stone })
hi("VisualNOS", { bg = stone })
hi("Search", { fg = ink, bg = t.hot })
hi("IncSearch", { fg = ink, bg = t.accent })
hi("CurSearch", { fg = ink, bg = t.accent })
hi("Substitute", { fg = ink, bg = t.glow2 })
hi("MatchParen", { fg = t.hot, bg = air5, bold = true })
hi("NonText", { fg = stone })
hi("Whitespace", { fg = stone })
hi("EndOfBuffer", { fg = bg })
hi("Conceal", { fg = soft })
hi("Directory", { fg = t.glow3 })
hi("Title", { fg = t.hot, bold = true })
hi("ErrorMsg", { fg = alert })
hi("WarningMsg", { fg = t.accent })
hi("MoreMsg", { fg = t.glow1 })
hi("ModeMsg", { fg = t.hot })
hi("Question", { fg = t.glow1 })
hi("WildMenu", { fg = ink, bg = t.accent })
hi("QuickFixLine", { bg = air5 })
-- chrome: the status line is a bar, the tab line a tab strip
hi("StatusLine", { fg = text, bg = surface })
hi("StatusLineNC", { fg = soft, bg = air3 })
hi("TabLine", { fg = soft, bg = bg })
hi("TabLineFill", { bg = bg })
hi("TabLineSel", { fg = t.hot, bg = surface, bold = true })
hi("WinBar", { fg = soft, bg = bg })
hi("WinBarNC", { fg = stone_lit, bg = bg })
hi("Pmenu", { fg = text, bg = surface })
hi("PmenuSel", { fg = ink, bg = t.accent })
hi("PmenuSbar", { bg = air3 })
hi("PmenuThumb", { bg = stone })
hi("PmenuKind", { fg = t.glow3, bg = surface })
hi("PmenuExtra", { fg = soft, bg = surface })
-- the pieces of the status line (see init.lua)
hi("GlowgridMode", { fg = ink, bg = t.accent, bold = true })
hi("GlowgridModeInsert", { fg = ink, bg = t.glow1, bold = true })
hi("GlowgridModeVisual", { fg = ink, bg = t.glow2, bold = true })
hi("GlowgridModeReplace", { fg = ink, bg = alert, bold = true })
hi("GlowgridModeCommand", { fg = ink, bg = t.hot, bold = true })
hi("GlowgridFile", { fg = text, bg = surface, bold = true })
hi("GlowgridSoft", { fg = soft, bg = surface })
hi("GlowgridValue", { fg = t.glow3, bg = surface })
hi("GlowgridGood", { fg = t.glow1, bg = surface })
hi("GlowgridBad", { fg = alert, bg = surface })

-- syntax: keywords are the hottest light, numbers the second light, comments a muted violet
hi("Comment", { fg = comment, italic = true })
hi("Constant", { fg = t.glow1 })
hi("String", { fg = t.string })
hi("Character", { fg = t.string })
hi("Number", { fg = t.glow1 })
hi("Boolean", { fg = t.glow1 })
hi("Float", { fg = t.glow1 })
hi("Identifier", { fg = text })
hi("Function", { fg = t.glow3 })
hi("Statement", { fg = t.hot })
hi("Conditional", { fg = t.hot })
hi("Repeat", { fg = t.hot })
hi("Label", { fg = t.hot })
hi("Operator", { fg = soft })
hi("Keyword", { fg = t.hot })
hi("Exception", { fg = t.hot })
hi("PreProc", { fg = t.accent })
hi("Include", { fg = t.accent })
hi("Define", { fg = t.accent })
hi("Macro", { fg = t.accent })
hi("Type", { fg = t.type })
hi("StorageClass", { fg = t.hot })
hi("Structure", { fg = t.type })
hi("Typedef", { fg = t.type })
hi("Special", { fg = t.accent })
hi("SpecialChar", { fg = t.accent })
hi("Tag", { fg = t.hot })
hi("Delimiter", { fg = soft })
hi("SpecialComment", { fg = comment, bold = true })
hi("Debug", { fg = t.glow2 })
hi("Underlined", { fg = t.glow3, underline = true })
hi("Error", { fg = alert })
hi("Todo", { fg = ink, bg = t.hot, bold = true })

-- treesitter and LSP semantic tokens
hi("@variable", { fg = text })
hi("@variable.builtin", { fg = t.accent })
hi("@variable.parameter", { fg = prop })
hi("@variable.member", { fg = prop })
hi("@property", { fg = prop })
hi("@constant", { fg = t.glow1 })
hi("@constant.builtin", { fg = t.glow1 })
hi("@module", { fg = t.type })
hi("@string.escape", { fg = t.accent })
hi("@string.special", { fg = t.accent })
hi("@function", { fg = t.glow3 })
hi("@function.builtin", { fg = t.glow3 })
hi("@function.macro", { fg = t.accent })
hi("@constructor", { fg = t.type })
hi("@keyword", { fg = t.hot })
hi("@operator", { fg = soft })
hi("@punctuation.bracket", { fg = soft })
hi("@punctuation.delimiter", { fg = soft })
hi("@type", { fg = t.type })
hi("@type.builtin", { fg = t.type })
hi("@attribute", { fg = t.accent })
hi("@tag", { fg = t.hot })
hi("@tag.attribute", { fg = prop })
hi("@tag.delimiter", { fg = soft })
hi("@comment", { link = "Comment" })
hi("@markup.heading", { fg = t.hot, bold = true })
hi("@markup.link", { fg = t.glow3, underline = true })
hi("@markup.raw", { fg = t.glow1 })
hi("@markup.strong", { bold = true })
hi("@markup.italic", { italic = true })
hi("@markup.list", { fg = t.accent })
hi("@lsp.type.parameter", { fg = prop })
hi("@lsp.type.property", { fg = prop })
hi("@lsp.type.namespace", { fg = t.type })

-- diagnostics and diffs
hi("DiagnosticError", { fg = alert })
hi("DiagnosticWarn", { fg = t.accent })
hi("DiagnosticInfo", { fg = t.glow3 })
hi("DiagnosticHint", { fg = soft })
hi("DiagnosticOk", { fg = t.glow1 })
hi("DiagnosticUnderlineError", { undercurl = true, sp = alert })
hi("DiagnosticUnderlineWarn", { undercurl = true, sp = t.accent })
hi("DiagnosticUnderlineInfo", { undercurl = true, sp = t.glow3 })
hi("DiagnosticUnderlineHint", { undercurl = true, sp = soft })
hi("DiffAdd", { bg = "#16261d" })
hi("DiffChange", { bg = air3 })
hi("DiffDelete", { fg = alert, bg = "#2a1220" })
hi("DiffText", { bg = air5 })
hi("Added", { fg = t.glow1 })
hi("Changed", { fg = t.accent })
hi("Removed", { fg = alert })
hi("SpellBad", { undercurl = true, sp = alert })
hi("SpellCap", { undercurl = true, sp = t.accent })

-- the terminal inside Neovim uses the same sixteen colours as the desktop terminal
local ansi = { surface, alert, t.glow1, t.hot, t.glow3, t.glow2, "#8fe3f7", text, "#5a3d52", "#ff8a80", "#b8ff9a", "#ffe49c", "#8fdcf5", "#ffb8f4", "#bdf0ff", "#ffffff" }
for i, c in ipairs(ansi) do vim.g["terminal_color_" .. (i - 1)] = c end
