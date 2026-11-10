# Part 3: Flakes

A flake is a folder with a flake.nix that names its inputs exactly and lists what it offers. Lock the inputs and the same flake builds the same thing on any machine, today or in five years.

## Chapter 8. Why flakes exist

Plain Nix has a hole in its reproducibility. An expression like `import <nixpkgs> { }` asks the machine "which Nixpkgs do you have?". The answer comes from `NIX_PATH` and channels, which differ between machines and change whenever someone runs `nix-channel --update`. Two people with the same `configuration.nix` can build different systems.

Flakes close the hole with three rules:

1. **Every input is named in the file**, with a URL: `github:NixOS/nixpkgs/nixos-26.05`.
2. **Every input is locked** in `flake.lock` to one exact commit and content hash.
3. **Evaluation is pure**: no `<nixpkgs>`, no environment variables, no files outside the flake, no `builtins.currentSystem`.

The result: `git clone` plus `nix build` gives the same output path on every machine, as long as the lock file is the same.

| | Channels | Flakes |
| --- | --- | --- |
| Where the Nixpkgs version lives | on the machine (`nix-channel`) | in your repo (`flake.lock`) |
| Same result on another machine | not guaranteed | yes |
| Update | `nix-channel --update` | `nix flake update` |
| Roll back an update | rebuild an old generation | `git checkout flake.lock` |
| Several versions of Nixpkgs at once | awkward | normal: one input each |
| A standard way to publish packages, shells, systems | no | yes: the outputs schema |

### Turning flakes on

Flakes and the new `nix` command are still marked experimental, but they are stable in practice and used by most of the community. Enable them once:

```nix
nix.settings.experimental-features = [ "nix-command" "flakes" ];
```

On a machine without NixOS, put `experimental-features = nix-command flakes` in `~/.config/nix/nix.conf`.

### The new nix command

Flakes come with one command that has subcommands. A flake reference names a flake and, after `#`, one of its outputs.

| Command | What it does |
| --- | --- |
| `nix run nixpkgs#cowsay -- hi` | run a program without installing it |
| `nix shell nixpkgs#ripgrep nixpkgs#jq` | a shell with these on PATH |
| `nix build .#mytool` | build an output; result appears as `./result` |
| `nix develop` | enter this flake's development shell |
| `nix flake init -t templates#go-hello` | start a new flake from a template |
| `nix flake show` | list a flake's outputs |
| `nix flake metadata` | show inputs and locked revisions |
| `nix flake update` | update every input in the lock file |
| `nix flake check` | evaluate everything and run the checks |
| `nix search nixpkgs ripgrep` | search packages |

Flake references you will see: `.` (this folder), `github:owner/repo`, `github:owner/repo/branch-or-tag`, `git+https://example.org/repo.git`, `path:/some/folder`, and registry names like `nixpkgs` (which means `github:NixOS/nixpkgs/nixpkgs-unstable` unless you pin it).

::: {.exer t="Exercises"}
1. Why does `import <nixpkgs> { }` fail inside a flake?
2. Run `htop` once without installing it.

*Answers* 1 Pure evaluation forbids looking up `NIX_PATH`; inputs must be declared in `flake.nix`. 2 `nix run nixpkgs#htop`.
:::

## Chapter 9. Anatomy of a flake

A `flake.nix` is one attribute set with three keys: a **description**, the **inputs** it depends on, and **outputs**, a function that gets the fetched inputs and returns everything the flake provides.

```nix
{
  description = "My machines and tools";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages.${system}.default = pkgs.hello;
      devShells.${system}.default = pkgs.mkShell {
        packages = [ pkgs.go pkgs.gopls ];
      };
      nixosConfigurations.frost = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/frost/configuration.nix ];
      };
    };
}
```

`self` is the flake itself, so outputs can refer to each other (`self.packages.${system}.default`). `nixpkgs.legacyPackages.${system}` is the usual package set; the odd name is historical.

### Inputs

```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  home-manager = {
    url = "github:nix-community/home-manager/release-26.05";
    inputs.nixpkgs.follows = "nixpkgs";  # use our nixpkgs, not its own
  };
  wallpapers = { url = "github:ana/wallpapers"; flake = false; };  # plain source
};
```

**follows** makes an input reuse another input instead of locking its own copy. Without it, Home Manager would bring a second Nixpkgs: more downloads, and two versions of glibc in one system. **flake = false** fetches any repo as a source folder; use it as `inputs.wallpapers` (a path) in your outputs.

### The outputs schema

Nix commands look for outputs by name. Most are per system, because a package for `x86_64-linux` differs from one for `aarch64-darwin`.

::: {.worked t="Which command reads which output"}
| Output | Read by |
| --- | --- |
| `packages.<sys>.<name>` | `nix build .#name` |
| `apps.<sys>.<name>` | `nix run .#name` |
| `devShells.<sys>.<name>` | `nix develop .#name` |
| `nixosConfigurations.<host>` | `nixos-rebuild switch --flake .#host` |
| `homeConfigurations.<user>` | `home-manager switch --flake .#user` |
| `checks.<sys>.<name>` | `nix flake check` |
| `formatter.<sys>` | `nix fmt` |
| `overlays.<name>` | other flakes, in their nixpkgs |
| `nixosModules.<name>` | other flakes, in their modules list |
| `templates.<name>` | `nix flake init -t .#name` |

`.#name` means "this folder's flake, output `name`". With no name, Nix looks for `default`.
:::

### flake.lock

The first command that evaluates the flake writes `flake.lock`. It is plain JSON; you never edit it by hand, but you should be able to read it.

```text
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1761800000,
        "narHash": "sha256-Qw3...=",
        "owner": "NixOS", "repo": "nixpkgs",
        "rev": "9b6e1d2c...", "type": "github"
      },
      "original": { "owner": "NixOS", "ref": "nixos-26.05",
                    "repo": "nixpkgs", "type": "github" }
    },
    "root": { "inputs": { "nixpkgs": "nixpkgs" } }
  },
  "root": "root", "version": 7
}
```

**original** is what you asked for (a branch). **locked** is what you got (one commit, one hash). Commit `flake.lock` next to `flake.nix`: it is the reproducibility.

::: {.pit t="The flake only sees files Git knows"}
You add `hosts/frost/configuration.nix`, rebuild, and get `error: getting status of '/nix/store/...-source/hosts/frost/configuration.nix': No such file or directory`. In a Git repo, Nix copies only tracked files into the store. Run `git add` on the new file; you do not need to commit. The same rule keeps secrets that Git ignores out of the store.
:::

::: {.exer t="Exercises"}
1. Add an input `nixos-hardware` from `github:NixOS/nixos-hardware`. Does it need `follows`?
2. What runs for `nix run .#` when the flake has `apps.x86_64-linux.default`?
3. Where in `flake.lock` do you find the commit your system is built from?

*Answers* 1 `inputs.nixos-hardware.url = "github:NixOS/nixos-hardware";`. It has no nixpkgs input of its own, so no follows is needed. 2 That default app, on an x86_64 Linux machine. 3 `nodes.nixpkgs.locked.rev`.
:::

## Chapter 10. Your machines as a flake

One Git repo can describe every machine you own. Here is a layout that grows well.

```text
nix-config/
├── flake.nix
├── flake.lock
├── hosts/
│   ├── frost/   configuration.nix  hardware-configuration.nix
│   └── ember/   configuration.nix  hardware-configuration.nix
├── modules/     common.nix  desktop.nix  server.nix  backup.nix
└── home/        ana.nix
```

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager/release-26.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs = inputs@{ self, nixpkgs, home-manager, ... }:
    let
      mkHost = name: extra: nixpkgs.lib.nixosSystem {
        specialArgs = { inherit inputs; };  # every module may take `inputs`
        modules = [
          ./hosts/${name}/configuration.nix
          ./modules/common.nix
          home-manager.nixosModules.home-manager
        ] ++ extra;
      };
    in {
      nixosConfigurations = {
        frost = mkHost "frost" [ ./modules/desktop.nix ];
        ember = mkHost "ember" [ ./modules/server.nix ./modules/backup.nix ];
      };
    };
}
```

`mkHost` is just a function: plain Nix, no magic. The CPU type comes from `nixpkgs.hostPlatform`, which `hardware-configuration.nix` sets, so `nixosSystem` needs no `system` argument.

### specialArgs and inputs in modules

`specialArgs` adds arguments to every module. With `inputs` passed in, any module can reach any input:

```nix
# modules/common.nix
{ inputs, pkgs, ... }:
let unstable = inputs.nixpkgs-unstable.legacyPackages.${pkgs.stdenv.hostPlatform.system}; in {
  environment.systemPackages = [ pkgs.git unstable.neovim ];  # mix stable and unstable
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  nix.registry.nixpkgs.flake = inputs.nixpkgs;  # recent NixOS does this for you
}
```

To allow unfree packages from the unstable set, import it instead: `import inputs.nixpkgs-unstable { system = pkgs.stdenv.hostPlatform.system; config.allowUnfree = true; }`.

### Building and switching

::: {.term t="Rebuild from the flake"}
```sh
$ cd ~/nix-config
$ sudo nixos-rebuild switch --flake .#frost
$ sudo nixos-rebuild switch --flake .         # .# defaults to this hostname
$ nixos-rebuild build --flake .#ember         # build another host locally
$ nixos-rebuild switch --flake .#ember \
    --target-host ana@ember --use-remote-sudo  # build here, deploy over SSH
```
:::

Newer releases spell `--use-remote-sudo` as `--sudo`. If `/etc/nixos/flake.nix` exists, a bare `sudo nixos-rebuild switch` uses it with the machine's hostname. Many people instead keep the repo in their home folder and link it: `sudo ln -s ~/nix-config/flake.nix /etc/nixos/flake.nix`.

::: {.tip t="Show the Git commit in the system"}
Add `system.configurationRevision = self.rev or self.dirtyRev or null;` (pass `self` through `specialArgs`). Then `nixos-version --configuration-revision` tells you which commit the running system came from.
:::

::: {.exer t="Exercises"}
1. Add a third host `pi` that uses `./modules/server.nix`.
2. How does `modules/common.nix` get the `inputs` argument?

*Answers* 1 `pi = mkHost "pi" [ ./modules/server.nix ];` plus `hosts/pi/` with its own hardware file (which sets `nixpkgs.hostPlatform = "aarch64-linux";`). 2 From `specialArgs = { inherit inputs; };` in `nixosSystem`.
:::

## Chapter 11. Dev shells and per-project tools

On NixOS you do not install compilers globally. Each project carries a flake that describes its tools, and `nix develop` puts them on PATH. A new laptop, a colleague or a CI server gets exactly the same versions.

```nix
{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f nixpkgs.legacyPackages.${s});
    in {
      devShells = forAll (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [ go gopls golangci-lint postgresql_16 ];
          env.DATABASE_URL = "postgres://localhost/app_dev";
          shellHook = ''
            echo "go $(go version | cut -d' ' -f3) ready"
          '';
        };
      });
    };
}
```

`forAll` builds the same shell for every listed system: `devShells.x86_64-linux.default`, `devShells.aarch64-darwin.default`, and so on.

::: {.term t="Using the shell"}
```sh
$ nix develop
go go1.25.3 ready
$ which go
/nix/store/...-go-1.25.3/bin/go
$ exit
$ nix develop -c go test ./...   # run one command inside the shell
```
:::

### Shells for common languages

| Language | packages = with pkgs; [ ... ] |
| --- | --- |
| Python | `(python3.withPackages (ps: [ ps.requests ps.pytest ])) ruff` |
| Rust | `cargo rustc rust-analyzer clippy rustfmt` |
| Node | `nodejs_22 pnpm` |
| C and C++ | `gcc cmake pkg-config openssl` (headers come with them) |
| Go | `go gopls delve` |

Use `inputsFrom = [ self.packages.${system}.default ];` to get every build input of your own package without listing them again.

### direnv: shells that load themselves

```nix
programs.direnv = { enable = true; nix-direnv.enable = true; };  # in NixOS or Home Manager
```

In the project folder, write a one-line `.envrc` containing `use flake` and run `direnv allow`. From then on, entering the folder loads the shell and leaving unloads it. nix-direnv caches the result and protects it from garbage collection, so it is instant after the first time.

::: {.pit t="A dev shell is not a container"}
`nix develop` only changes environment variables. Your home folder, network and system services are the same as outside. Programs outside the shell cannot see its tools, so point your editor at the shell (most support direnv).
:::

::: {.exer t="Exercises"}
1. Write a dev shell with Python 3, `numpy` and `pandas`.
2. What does `nix develop -c make` do?

*Answers* 1 `pkgs.mkShell { packages = [ (pkgs.python3.withPackages (ps: [ ps.numpy ps.pandas ])) ]; }`. 2 Enters the dev shell, runs `make` in it, and exits.
:::

## Chapter 12. Locking, updating and flake patterns

### Updating

::: {.term t="Move the lock file forward"}
```sh
$ nix flake update                  # every input
$ nix flake update nixpkgs          # only one input
• Updated input 'nixpkgs':
    'github:NixOS/nixpkgs/3f0a8ac' (2026-09-14)
  → 'github:NixOS/nixpkgs/9b6e1d2' (2026-10-30)
$ sudo nixos-rebuild switch --flake .
$ git commit -am "update nixpkgs"
```
:::

If the update breaks something, `git checkout flake.lock` and rebuild. On older Nix (before 2.19), updating one input was written `nix flake lock --update-input nixpkgs`.

### Pinning and overriding

```nix
inputs.nixpkgs.url = "github:NixOS/nixpkgs/9b6e1d2c4f...";   # one exact commit
```

```sh
$ nix build --override-input nixpkgs github:NixOS/nixpkgs/nixos-unstable
$ nix flake lock --override-input mylib path:/home/ana/src/mylib  # test a local checkout
```

### Upgrading to a new release

Change the branch names in the inputs (`nixos-26.05` to `nixos-26.11`, and `release-26.05` to `release-26.11` for Home Manager), run `nix flake update`, read the release notes for removed options, rebuild. Do not touch `system.stateVersion`.

### Patterns you will meet

**flake-utils** removes the per-system boilerplate:

```nix
outputs = { nixpkgs, flake-utils, ... }:
  flake-utils.lib.eachDefaultSystem (system:
    let pkgs = nixpkgs.legacyPackages.${system}; in {
      packages.default = pkgs.callPackage ./package.nix { };
      devShells.default = pkgs.mkShell { inputsFrom = [ (pkgs.callPackage ./package.nix { }) ]; };
    });
```

**flake-parts** is a module system for flakes: you write `perSystem = { pkgs, ... }: { packages.default = ...; };` and it fills in the systems. It suits large flakes with many parts.

**A plain helper** like `forAll` from Chapter 11 needs no extra input and is easy to read. Start there.

### Checks and formatting

```nix
formatter.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.nixfmt;
checks.x86_64-linux.frost = self.nixosConfigurations.frost.config.system.build.toplevel;
```

`nix fmt` now formats your files, and `nix flake check` fails if host `frost` no longer builds. Run it before every push.

::: {.worked t="Pick the right tool"}
| You want to | Use |
| --- | --- |
| try a program once | `nix run nixpkgs#name` |
| a few tools for this terminal | `nix shell nixpkgs#a nixpkgs#b` |
| tools for one project, for everyone | `devShells` + `nix develop` or direnv |
| a program always available to you | Home Manager `home.packages` |
| a program for every user, or a service | NixOS `environment.systemPackages`, `services.*` |
:::

::: {.exer t="Exercises"}
1. Update only Home Manager.
2. A teammate's build differs from yours. What do you compare first?
3. Make `nix flake check` build host `ember`.

*Answers* 1 `nix flake update home-manager`. 2 `flake.lock`: if the locked revisions differ, the inputs differ. Then uncommitted changes (`git status`). 3 `checks.x86_64-linux.ember = self.nixosConfigurations.ember.config.system.build.toplevel;`
:::
