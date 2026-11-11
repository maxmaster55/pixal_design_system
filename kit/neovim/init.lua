-- Neovim, Glowgrid style. Small on purpose: sensible defaults, the colour scheme, a status
-- line built like the desktop bar, square borders everywhere, and treesitter highlighting.
-- This file is linked from the repo (glowgrid/neovim/init.lua), so edits apply on restart.

vim.g.mapleader = " "

local o = vim.opt
o.number = true
o.relativenumber = true
o.cursorline = true
o.signcolumn = "yes"
o.termguicolors = true
o.expandtab = true
o.shiftwidth = 2
o.tabstop = 2
o.smartindent = true
o.ignorecase = true
o.smartcase = true
o.scrolloff = 6
o.splitright = true
o.splitbelow = true
o.undofile = true
o.updatetime = 300
o.clipboard = "unnamedplus"      -- yank and paste use the desktop clipboard (wl-clipboard)
o.mouse = "a"
o.showmode = false               -- the status line shows the mode
o.laststatus = 3                 -- one status line for the whole window, like the bar
o.fillchars = { eob = " ", vert = "│", horiz = "─" }
o.list = true
o.listchars = { tab = "· ", trail = "·", nbsp = "␣" }
o.winborder = "single"           -- square borders on every floating window
-- a block cursor that blinks in two held steps, an underline while replacing
o.guicursor = "n-v-c-sm:block-blinkwait500-blinkon500-blinkoff500,i-ci-ve:ver25-blinkwait500-blinkon500-blinkoff500,r-cr-o:hor20"

vim.cmd.colorscheme("glowgrid")

-- re-read the palette when the desktop theme changes (glowgrid-theme ember|forge|frost)
local theme_file = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/glowgrid/theme"
local watcher = vim.uv.new_fs_event()
if watcher and vim.uv.fs_stat(theme_file) then
  watcher:start(theme_file, {}, vim.schedule_wrap(function() vim.cmd.colorscheme("glowgrid") end))
end

-- ---- status line: mode cell, file, then values on the right, as on the desktop bar ----
local modes = {
  n = { "NORMAL", "GlowgridMode" }, i = { "INSERT", "GlowgridModeInsert" }, v = { "VISUAL", "GlowgridModeVisual" },
  V = { "V-LINE", "GlowgridModeVisual" }, ["\22"] = { "V-BLOCK", "GlowgridModeVisual" }, R = { "REPLACE", "GlowgridModeReplace" },
  c = { "COMMAND", "GlowgridModeCommand" }, t = { "TERMINAL", "GlowgridModeInsert" }, s = { "SELECT", "GlowgridModeVisual" },
}
function _G.glowgrid_statusline()
  local m = modes[vim.fn.mode()] or modes.n
  local diag = ""
  local errors = #vim.diagnostic.get(0, { severity = vim.diagnostic.severity.ERROR })
  local warns = #vim.diagnostic.get(0, { severity = vim.diagnostic.severity.WARN })
  if errors > 0 then diag = diag .. "%#GlowgridBad# " .. errors .. " ERR " end
  if warns > 0 then diag = diag .. "%#GlowgridSoft# " .. warns .. " WARN " end
  local branch = vim.b.gitsigns_head or ""
  return table.concat({
    "%#", m[2], "# ", m[1], " ",
    "%#GlowgridFile# %f %#GlowgridBad#%m%#GlowgridSoft#%r",
    "%=", diag,
    branch ~= "" and ("%#GlowgridGood# " .. branch .. " ") or "",
    "%#GlowgridSoft# %{&filetype} ",
    "%#GlowgridValue# %l:%c ",
    "%#GlowgridSoft# %p%% ",
  })
end
o.statusline = "%!v:lua.glowgrid_statusline()"

-- ---- diagnostics: square signs, no rounded popups ----
vim.diagnostic.config({
  virtual_text = { prefix = "■" },
  signs = { text = { [vim.diagnostic.severity.ERROR] = "■", [vim.diagnostic.severity.WARN] = "■", [vim.diagnostic.severity.INFO] = "■", [vim.diagnostic.severity.HINT] = "■" } },
  float = { border = "single" },
  severity_sort = true,
})

-- ---- treesitter highlighting for the languages installed by Nix ----
vim.api.nvim_create_autocmd("FileType", {
  callback = function(ev) pcall(vim.treesitter.start, ev.buf) end,
})

-- ---- a few keys ----
local map = vim.keymap.set
map("n", "<Esc>", "<cmd>nohlsearch<cr>", { desc = "Clear search highlight" })
map("n", "<leader>w", "<cmd>write<cr>", { desc = "Save" })
map("n", "<leader>q", "<cmd>quit<cr>", { desc = "Quit" })
map("n", "<leader>e", "<cmd>Explore<cr>", { desc = "File explorer" })
map("n", "<leader>d", vim.diagnostic.open_float, { desc = "Show diagnostic" })
map({ "n", "v" }, "<leader>y", '"+y', { desc = "Copy to clipboard" })
map("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Leave terminal mode" })

-- highlight what was just yanked for two frames
vim.api.nvim_create_autocmd("TextYankPost", { callback = function() vim.hl.on_yank({ higroup = "IncSearch", timeout = 166 }) end })

-- git change markers in the sign column, as square cells (plugin installed by Nix)
pcall(function()
  require("gitsigns").setup({
    signs = { add = { text = "▌" }, change = { text = "▌" }, delete = { text = "▁" }, topdelete = { text = "▔" }, changedelete = { text = "▌" } },
  })
end)
