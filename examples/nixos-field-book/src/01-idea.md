# Part 1: The Nix idea

Three chapters on the ground floor: what Nix stores and why, the small language you write it in, and how a recipe becomes a folder in the store.

## Chapter 1. Nix, Nixpkgs and NixOS

Three names, three things. Keep them apart from the first page.

| Name | What it is |
| --- | --- |
| **Nix** | the package manager and build tool, and the language its recipes are written in |
| **Nixpkgs** | one huge Git repository of recipes: over 100,000 packages plus all NixOS modules |
| **NixOS** | a Linux distribution whose whole system is built by Nix from your configuration |

### The store

Everything Nix builds lives in `/nix/store`, one folder per build, named `hash-name-version`. The hash covers every input: source, dependencies, compiler flags, build script. Programs refer to their libraries by full store path, never by `/usr/lib`.

```text
/nix/store/
├── 2b1k...-glibc-2.40/
├── 9lsj...-git-2.47.1/
│   └── bin/git          # linked against /nix/store/2b1k...-glibc-2.40
├── xq7c...-git-2.48.0/  # a newer git sits beside the old one
└── a0m4...-nixos-system-frost-26.05/
```

This gives Nix its five guarantees:

1. **No conflicts.** Two versions of one library never fight over one file name.
2. **Atomic upgrades.** A new version is built off to the side; switching is a single symlink change.
3. **Rollbacks.** The old version is still in the store until you delete it.
4. **Reproducible builds.** Same inputs give the same output path on any machine.
5. **Complete dependencies.** If a package builds, nothing it needs is missing, because builds run in a sandbox that sees only declared inputs.

The store is **read-only**. You never edit files in it; you change the recipe and build again.

### Profiles and generations

A **profile** is a symlink that points at one store path. Each time you change it, Nix keeps the old target as a numbered **generation**.

```text
/nix/var/nix/profiles/system      -> system-42-link
/nix/var/nix/profiles/system-41-link -> /nix/store/...-nixos-system-frost-26.05...
/nix/var/nix/profiles/system-42-link -> /nix/store/...-nixos-system-frost-26.05...
/run/current-system               -> the generation now running
```

Booting an older generation from the boot menu, or running `nixos-rebuild switch --rollback`, just moves the symlink back.

### Declarative, not imperative

On most systems you run commands that change the machine (`apt install`, edit `/etc/ssh/sshd_config`, `systemctl enable`). The machine's state is the sum of everything anyone ever did to it. On NixOS you write down what the machine should be, in `/etc/nixos/configuration.nix`, and Nix builds that. The file is the truth.

```nix
{ pkgs, ... }: {
  environment.systemPackages = [ pkgs.git pkgs.htop ];
  services.openssh.enable = true;
}
```

Remove a line and rebuild, and the package or service is gone, with no leftover config files.

::: {.exer t="Exercises"}
1. Name the three things called Nix, Nixpkgs and NixOS in one line each.
2. Why can two versions of OpenSSL be installed at the same time?
3. You upgrade and the new kernel will not boot. What do you do?

*Answers* 1 The package manager and its language; the collection of recipes and modules; the Linux distribution built by Nix. 2 Each lives in its own store folder with a different hash, and each program refers to the exact one it was built with. 3 Pick the previous generation in the boot menu, then run `sudo nixos-rebuild switch --rollback` or fix the config.
:::

## Chapter 2. The Nix language

Nix is a small, **lazy**, **pure**, **functional** language. Pure: an expression cannot change anything or read the clock, so the same expression always gives the same value. Lazy: nothing is computed until it is needed. You will write mostly one kind of value: the attribute set.

### Values

| Type | Examples |
| --- | --- |
| string | `"hello"`, `"v${version}"` |
| multi-line string | `''` ... `''` (strips common indentation) |
| integer, float | `42`, `3.14` |
| boolean, null | `true`, `false`, `null` |
| path | `./hosts/frost.nix`, `/etc/hosts` (no quotes) |
| list | `[ 1 "two" ./three ]` (space separated) |
| attribute set | `{ a = 1; b.c = 2; }` |
| function | `x: x + 1` |

### Attribute sets

An attribute set maps names to values. Every binding ends with `;`. A dotted name is a shortcut for nested sets.

```nix
{
  name = "frost";
  services.openssh.enable = true;   # same as services = { openssh = { enable = true; }; };
}
```

Read with a dot, test with `?`, give a fallback with `or`, merge with `//`.

::: {.worked t="Evaluate the set operators"}
```nix
let s = { a = 1; b = { c = 2; }; }; in [
  s.b.c                 # 2
  (s ? a)               # true
  (s.z or 0)            # 0: z is missing
  (s // { a = 9; })     # { a = 9; b = { c = 2; }; }
  (s // { b = { d = 3; }; })  # { a = 1; b = { d = 3; }; }
]
```
The last line is the trap: `//` is a **shallow** merge. The right side replaces `b` whole, so `c` is lost. NixOS modules merge deeply; `//` does not.
:::

### let, with, inherit, rec

```nix
let
  version = "1.4";
  pkgs = import <nixpkgs> { };
in {
  inherit version;                 # version = version;
  inherit (pkgs) git htop;         # git = pkgs.git; htop = pkgs.htop;
  tools = with pkgs; [ curl jq ];  # names looked up in pkgs
  label = "tool-${version}";       # string interpolation
}
```

`rec { a = 1; b = a + 1; }` lets bindings in one set see each other. Prefer `let`: `rec` makes it easy to write infinite loops by accident. Keep `with` small and local; a big `with` hides where names come from.

### Functions

A function has one argument and a body: `x: x * 2`. More arguments are written as functions that return functions: `a: b: a + b`. Most Nix functions instead take one **attribute set** and pull it apart:

```nix
let
  greet = { name, greeting ? "Hello", ... }:  # default value, ... allows extra keys
    "${greeting}, ${name}!";
in greet { name = "Ana"; }                     # "Hello, Ana!"
```

Every NixOS module and every package file is such a function. `{ config, pkgs, lib, ... }:` at the top of a file is an argument pattern, nothing more. Write `args@{ pkgs, ... }:` to also keep the whole set as `args`.

Calling a function is just a space: `f x`. That is why lists need care.

::: {.pit t="Function calls inside lists"}
`[ f x ]` is a list of **two** items, `f` and `x`. To put the result of a call in a list, wrap it: `[ (f x) ]`. The same goes for `[ pkgs.python3.withPackages (ps: [ ps.requests ]) ]`, which needs parentheses around the whole call.
:::

### Strings, paths and interpolation

Inside `"..."` or `''...''`, `${expr}` inserts a value. Interpolating a package gives its store path, which is how configs point at programs:

```nix
ExecStart = "${pkgs.restic}/bin/restic backup /home";
# becomes "/nix/store/4kd...-restic-0.17.3/bin/restic backup /home"
```

A path like `./script.sh` is copied into the store when you interpolate it, so the result works on any machine. In `''` strings, write `''${` to get a literal `${` (useful in shell scripts).

### if, assert, import

```nix
if stdenv.isLinux then "linux" else "other"     # if always needs else
assert version != ""; "ok"                      # fail early with a clear error
import ./hosts/frost.nix                        # evaluate another file
```

`import` reads a file and returns its value. If the file holds a function, you still have to call it: `import ./greet.nix { name = "Ana"; }`.

### builtins and lib

`builtins` is always there: `builtins.map`, `builtins.filter`, `builtins.length`, `builtins.attrNames`, `builtins.toString`, `builtins.readFile`, `builtins.toJSON`. `lib` comes from Nixpkgs and has the helpers you will use daily:

| Function | Example and result |
| --- | --- |
| `lib.optional c x` | `lib.optional true "a"` gives `[ "a" ]`, false gives `[ ]` |
| `lib.optionals c xs` | same, for a whole list |
| `lib.mapAttrs f s` | `lib.mapAttrs (n: v: v * 2) { a = 1; }` gives `{ a = 2; }` |
| `lib.genAttrs ns f` | `lib.genAttrs [ "x" "y" ] (n: n)` gives `{ x = "x"; y = "y"; }` |
| `lib.concatStringsSep` | `lib.concatStringsSep "," [ "a" "b" ]` gives `"a,b"` |
| `lib.recursiveUpdate` | deep version of `//` |
| `lib.mkIf`, `lib.mkDefault` | module helpers (Chapter 5) |

### Laziness

Nix computes a value only when something asks for it. `let x = throw "boom"; in 1` is `1`, because `x` is never used. This is what lets Nixpkgs be one enormous set of 100,000 packages that loads in a second: you only pay for the attributes you touch.

::: {.term t="Try it in the REPL"}
```sh
$ nix repl
nix-repl> { a = 1; } // { b = 2; }
{ a = 1; b = 2; }
nix-repl> map (x: x * x) [ 1 2 3 ]
[ 1 4 9 ]
nix-repl> :lf nixpkgs
nix-repl> legacyPackages.x86_64-linux.git.version
"2.47.1"
```
:::

::: {.exer t="Exercises"}
1. What is `{ a.b = 1; } // { a.c = 2; }`?
2. How many items does `[ builtins.toString 5 ]` have?
3. Write a function `double` that takes `{ n }` and returns `n * 2`, then call it with 21.
4. What is `let f = { x ? 3, ... }: x; in f { y = 1; }`?
5. Rewrite `{ git = pkgs.git; jq = pkgs.jq; }` with `inherit`.

*Answers* 1 `{ a = { c = 2; }; }`: shallow merge replaces `a`. 2 Two: the function and the number. Use `[ (builtins.toString 5) ]`. 3 `let double = { n }: n * 2; in double { n = 21; }` gives 42. 4 `3`: `x` takes its default and `...` accepts `y`. 5 `{ inherit (pkgs) git jq; }`.
:::

## Chapter 3. Derivations, closures and caches

A **derivation** is a build recipe that Nix can run: a name, a system, a builder program, its arguments, environment variables and inputs. Every package in Nixpkgs ends as a derivation. You rarely write the raw form, but seeing it once explains everything else.

```nix
derivation {
  name = "hello-file";
  system = "x86_64-linux";
  builder = "/bin/sh";
  args = [ "-c" "echo hello > $out" ];
}
```

Nix writes this recipe to the store as a `.drv` file, then runs the builder in a sandbox with no network and an empty home. The variable `$out` is the output path the build must create. The two steps have names:

| Step | Input | Output | Command |
| --- | --- | --- | --- |
| **evaluate** | Nix code | `.drv` file | `nix eval`, `nix derivation show` |
| **realise** (build) | `.drv` file | store path | `nix build`, `nix-store --realise` |

### Closures

A store path's **closure** is the path plus everything it refers to, recursively. Copying a closure to another machine gives that machine everything needed to run the program, and nothing more.

::: {.term t="Inspect a closure"}
```sh
$ nix path-info -rSh nixpkgs#hello | tail -3
/nix/store/...-glibc-2.40-66          31.2M
/nix/store/...-hello-2.12.1           32.6M
$ nix why-depends nixpkgs#hello nixpkgs#glibc
/nix/store/...-hello-2.12.1
└───/nix/store/...-glibc-2.40-66
```
:::

Nix finds runtime dependencies by scanning the output for the hashes of its inputs. A compiler used only at build time leaves no trace in the output, so it is not in the runtime closure.

### Binary caches

Because the output path is known before building, Nix can ask a **binary cache** whether someone already built it. The official cache, `https://cache.nixos.org`, holds almost every package for the stable and unstable branches. If the path is there, Nix downloads it (a **substitute**) instead of building. Results are signed, and Nix checks the signature against `trusted-public-keys`.

```nix
nix.settings = {
  substituters = [ "https://cache.nixos.org" "https://nix-community.cachix.org" ];
  trusted-public-keys = [
    "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
    "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
  ];
};
```

If you change a package (a patch, a different flag), its hash changes, no cache has it, and you build it yourself. That is the price of customizing.

### Garbage collection

Nothing is deleted while something points to it. Those pointers are **GC roots**: profile generations, `result` symlinks from `nix build`, and running processes. Everything else can be collected.

```sh
$ nix-collect-garbage                  # delete unreachable paths
$ sudo nix-collect-garbage -d          # also delete old generations first
```

::: {.pit t="Old generations keep everything alive"}
Each generation is a GC root, so 80 old generations can hold 50 GB. Running `nix-collect-garbage` without `-d` frees little. Chapter 7 shows how to let the system clean itself on a schedule.
:::

::: {.exer t="Exercises"}
1. What is the difference between evaluating and realising?
2. You add a patch to `curl`. Why does your next rebuild take long?
3. Why is `gcc` not in the runtime closure of `hello`?

*Answers* 1 Evaluating turns Nix code into a `.drv` recipe; realising runs the recipe and produces the output path. 2 The patch changes the input hash, so the cache has no build of that exact curl; it and everything depending on it must be built locally. 3 The output of `hello` contains no reference to the gcc store path; only build-time inputs used it.
:::
