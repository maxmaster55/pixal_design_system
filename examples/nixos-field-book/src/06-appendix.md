# Back: Cheat sheets and glossary

Keep these pages open beside you while you work through the book, or beside the keyboard later.

## Cheat sheets

### Old commands and new commands

| Job | Classic command | New `nix` command |
| --- | --- | --- |
| try a program once | `nix-shell -p htop --run htop` | `nix run nixpkgs#htop` |
| shell with tools | `nix-shell -p jq curl` | `nix shell nixpkgs#jq nixpkgs#curl` |
| project shell | `nix-shell` (shell.nix) | `nix develop` (flake.nix) |
| build | `nix-build` | `nix build` |
| install for your user | `nix-env -iA nixpkgs.jq` | `nix profile add nixpkgs#jq` |
| search | `nix-env -qaP jq` | `nix search nixpkgs jq` |
| evaluate | `nix-instantiate --eval -E '1+1'` | `nix eval --expr '1+1'` |
| REPL | `nix repl '<nixpkgs>'` | `nix repl` then `:lf nixpkgs` |
| collect garbage | `nix-collect-garbage -d` | `nix store gc` |
| show a derivation | `nix show-derivation` | `nix derivation show` |

On NixOS, prefer the declarative ways (systemPackages, Home Manager, dev shells) over `nix-env` and `nix profile`. Older Nix spells `nix profile add` as `nix profile install`.

### nixos-rebuild

| Subcommand | Effect |
| --- | --- |
| `switch` | build, activate, make default |
| `boot` | build, make default at next boot |
| `test` | build, activate until reboot |
| `build` | build to `./result` only |
| `build-vm` | build a QEMU VM of this config |
| `dry-build` | list what would be built or fetched |
| `--rollback` | go back one generation |
| `--flake .#host` | use a flake output |
| `--target-host u@h` | deploy to another machine |
| `--show-trace` | full evaluation trace on error |

### The language on one page

| Write | Means |
| --- | --- |
| `{ a = 1; b.c = 2; }` | attribute set (nested via dots) |
| `s.a`, `s ? a`, `s.a or 0` | select, test, select with default |
| `s1 // s2` | shallow merge, right side wins |
| `[ 1 2 (f x) ]` | list; calls need parentheses |
| `l1 ++ l2` | concatenate lists |
| `x: x + 1` | function of one argument |
| `{ a, b ? 2, ... }: a + b` | function taking a set, with default |
| `args@{ a, ... }:` | also bind the whole set |
| `let x = 1; in x` | local bindings |
| `inherit x; inherit (s) a b;` | copy names into a set |
| `with pkgs; [ git jq ]` | bring a set's names into scope |
| `rec { a = 1; b = a; }` | self-referencing set |
| `"v${toString n}"` | interpolation |
| `''` ... `''` | indented string; `''${` escapes |
| `./file.nix`, `<nixpkgs>` | path; search path (not in flakes) |
| `import ./f.nix` | evaluate a file |
| `if c then a else b` | always both branches |
| `assert c; e` | stop with an error if not `c` |

### Module helpers

| Helper | Does |
| --- | --- |
| `lib.mkIf c { ... }` | apply only if `c` |
| `lib.mkMerge [ a b ]` | combine several sets |
| `lib.mkDefault v` | priority 1000: weak value |
| `lib.mkForce v` | priority 50: strong value |
| `lib.mkOverride n v` | any priority |
| `lib.mkBefore`, `lib.mkAfter` | order list and text items |
| `lib.mkEnableOption "x"` | a bool option, default false |
| `lib.mkPackageOption pkgs "x" { }` | a package option, default `pkgs.x` |
| `lib.mkOption { type; default; description; }` | declare any option |

### Option types

| Type | Accepts |
| --- | --- |
| `types.bool`, `types.int`, `types.str` | the obvious |
| `types.port` | integer 0 to 65535 |
| `types.path`, `types.package` | a path; a derivation |
| `types.enum [ "a" "b" ]` | one of the listed values |
| `types.listOf t`, `types.attrsOf t` | a list or set of `t` |
| `types.nullOr t` | `t` or `null` |
| `types.submodule { options = ...; }` | a nested set with its own options |
| `types.lines` | strings joined by newlines when merged |

### Paths worth knowing

| Path | What lives there |
| --- | --- |
| `/etc/nixos/` | configuration.nix, hardware file, or flake.nix |
| `/nix/store/` | every build, read-only |
| `/nix/var/nix/profiles/system*` | system generations |
| `/run/current-system` | the running generation |
| `/run/booted-system` | the generation you booted |
| `/etc/static/` | generated `/etc` files from the store |
| `/run/secrets/`, `/run/agenix/` | decrypted secrets (sops-nix, agenix) |
| `~/.nix-profile`, `/etc/profiles/per-user/` | user packages |

### lib functions you will use

`lib.optional`, `lib.optionals`, `lib.optionalString`, `lib.mapAttrs`, `lib.mapAttrsToList`, `lib.genAttrs`, `lib.filterAttrs`, `lib.attrNames`, `lib.concatMap`, `lib.concatStringsSep`, `lib.recursiveUpdate`, `lib.getExe`, `lib.getName`, `lib.makeBinPath`, `lib.escapeShellArg`, `lib.fakeHash`, `lib.versionAtLeast`, `lib.hiPrio`.

## Glossary

**attribute set**: Nix's map of names to values, written `{ name = value; }`.

**binary cache**: a server holding prebuilt store paths; Nix downloads from it instead of building.

**callPackage**: calls a package function, filling its arguments from Nixpkgs.

**channel**: a named, updatable URL for a Nixpkgs version; the pre-flake way to pick versions.

**closure**: a store path plus everything it refers to, recursively.

**derivation**: a build recipe Nix can run; stored as a `.drv` file.

**dev shell**: an environment with a project's tools on PATH, entered with `nix develop`.

**evaluation**: running Nix code to get values and derivations, before any build.

**fixed-output derivation**: a build whose output hash is known in advance, so it may use the network (fetchers).

**flake**: a folder with `flake.nix` and `flake.lock`: declared, locked inputs and standard outputs.

**follows**: makes one flake input reuse another input instead of its own copy.

**GC root**: anything that keeps store paths from garbage collection: profiles, `result` links.

**generation**: one numbered version of a profile; the system's generations appear in the boot menu.

**Home Manager**: a module system for a user's packages and dotfiles.

**lazy**: values are computed only when needed.

**module**: a function returning `imports`, `options` and `config`; NixOS is built from thousands of them.

**nixpkgs**: the repository of package recipes and NixOS modules.

**option**: a typed setting declared by a module, like `services.nginx.enable`.

**overlay**: `final: prev: { ... }`, a function that changes or adds packages in Nixpkgs.

**override, overrideAttrs**: change a package's function arguments, or its derivation attributes.

**profile**: a symlink to a store path that keeps its history as generations.

**pure evaluation**: evaluation that may not read anything not declared, required in flakes.

**realise**: build a derivation, or fetch it from a cache, so its output path exists.

**specialArgs**: extra arguments given to every NixOS module.

**stateVersion**: the release that first created a machine's or user's data; not the version you run.

**store path**: `/nix/store/<hash>-<name>`, the address of one build output.

**substituter**: a binary cache Nix is allowed to download from.
