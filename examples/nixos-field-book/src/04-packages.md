# Part 4: Packages and beyond

Write your own packages, change the ones Nixpkgs gives you, manage your home folder the same way, and take NixOS to VMs, containers and remote machines.

## Chapter 13. Writing packages

Most packages are a call to `stdenv.mkDerivation`. It wraps the raw `derivation` from Chapter 3 with a standard build environment (a C compiler, make, coreutils, patching tools) and a fixed list of **phases**.

```nix
# package.nix
{ lib, stdenv, fetchFromGitHub, pkg-config, ncurses }:
stdenv.mkDerivation (finalAttrs: {
  pname = "tinytop";
  version = "1.3.0";
  src = fetchFromGitHub {
    owner = "ana";
    repo = "tinytop";
    rev = "v${finalAttrs.version}";
    hash = "sha256-8Jm0xK2b6xq3cGJ7sQ1pYkD4zR5vT9wE2nL6hU0aBcY=";
  };
  nativeBuildInputs = [ pkg-config ];  # tools that run during the build
  buildInputs = [ ncurses ];           # libraries the program links against
  makeFlags = [ "PREFIX=$(out)" ];
  meta = {
    description = "A tiny process viewer";
    license = lib.licenses.mit;
    mainProgram = "tinytop";
    platforms = lib.platforms.linux;
  };
})
```

Build it with `nix build --impure --expr 'with import <nixpkgs> { }; callPackage ./package.nix { }'`, or better from a flake: `packages.${system}.default = pkgs.callPackage ./package.nix { };`.

### The phases

| Phase | Default action | Typical override |
| --- | --- | --- |
| unpack | extract `src` and cd into it | `sourceRoot = "source/cli";` |
| patch | apply `patches` | `patches = [ ./fix-path.patch ];` |
| configure | run `./configure --prefix=$out` if present | `configureFlags`, or `cmake` in `nativeBuildInputs` |
| build | run `make` | `buildPhase = "...";` |
| check | `make check` if `doCheck = true` | `doCheck = false;` |
| install | `make install` | `installPhase` |
| fixup | strip binaries, fix shebangs and RPATHs | `dontStrip = true;` |

When you write a phase yourself, keep the hooks so other tools can attach to it:

```nix
installPhase = ''
  runHook preInstall
  install -Dm755 tinytop $out/bin/tinytop
  install -Dm644 tinytop.1 $out/share/man/man1/tinytop.1
  runHook postInstall
'';
```

### callPackage

`callPackage ./package.nix { }` reads the function's argument names (`lib`, `stdenv`, `fetchFromGitHub`, ...) and fills each one from Nixpkgs. The `{ }` lets you override any of them. That is why package files start with a list of what they need.

### Fetchers and hashes

| Fetcher | For |
| --- | --- |
| `fetchFromGitHub { owner; repo; rev; hash; }` | GitHub tarballs (fast) |
| `fetchurl { url; hash; }` | one file |
| `fetchzip { url; hash; }` | an archive, unpacked |
| `fetchgit { url; rev; hash; }` | any Git server |

Fetchers are **fixed-output derivations**: they may use the network, because you promise the hash of the result. To find the hash, write `hash = lib.fakeHash;`, build once and copy the "got" value from the error (Case 3 in Chapter 17).

### Language builders

Nixpkgs has a builder per ecosystem. Each one locks the project's own dependencies by a hash, so builds stay offline and reproducible.

```nix
# Go
buildGoModule { pname = "api"; version = "0.4.0"; src = ./.; vendorHash = "sha256-..."; }

# Rust
rustPlatform.buildRustPackage { pname = "ripx"; version = "1.0.0"; src = ./.; cargoHash = "sha256-..."; }

# Python
python3Packages.buildPythonApplication {
  pname = "notes"; version = "2.1"; src = ./.;
  pyproject = true;
  build-system = [ python3Packages.setuptools ];
  dependencies = with python3Packages; [ click requests ];
}
```

### Scripts and wrappers

```nix
writeShellApplication {
  name = "backup-now";
  runtimeInputs = [ rsync coreutils ];   # put on PATH for the script
  text = ''
    rsync -a /home/ "/mnt/usb/$(date +%F)/"
  '';
}
```

`writeShellApplication` also runs ShellCheck on the script at build time. To give an existing program extra PATH entries or variables, add `makeWrapper` to `nativeBuildInputs` and run `wrapProgram $out/bin/tool --prefix PATH : ${lib.makeBinPath [ git ]}` in `postInstall`.

### Prebuilt binaries

A program downloaded as a Linux binary expects `/lib64/ld-linux-x86-64.so.2` and libraries in `/usr/lib`. NixOS has neither. `autoPatchelfHook` rewrites the binary to use store paths:

```nix
stdenv.mkDerivation {
  pname = "vendor-tool"; version = "5.2";
  src = fetchurl { url = "https://example.com/vendor-tool-5.2.tar.gz"; hash = "sha256-..."; };
  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ stdenv.cc.cc.lib zlib openssl ];  # libraries it links to
  installPhase = "install -Dm755 vendor-tool $out/bin/vendor-tool";
}
```

::: {.exer t="Exercises"}
1. A library is needed at runtime. Does it go in `buildInputs` or `nativeBuildInputs`?
2. Package a shell script `./hello.sh` that needs `curl`.
3. Why does a fetcher get network access when normal builds do not?

*Answers* 1 `buildInputs`. `nativeBuildInputs` are tools that run on the build machine, like `pkg-config` or `cmake`. 2 `writeShellApplication { name = "hello"; runtimeInputs = [ curl ]; text = builtins.readFile ./hello.sh; }`. 3 It is a fixed-output derivation: the hash of its result is fixed in advance, so whatever it downloads must match or the build fails.
:::

## Chapter 14. Overrides and overlays

Sooner or later you want a package from Nixpkgs, but a little different: a newer version, a patch, a build option turned on.

### override: change the arguments

`override` calls the package's function again with some arguments replaced. Use it for the inputs in the `{ ... }:` at the top of the package file, often feature flags.

```nix
pkgs.ncmpcpp.override { visualizerSupport = true; }
pkgs.git.override { svnSupport = true; }
pkgs.hello.override { stdenv = pkgs.clangStdenv; }   # build with clang
```

### overrideAttrs: change the derivation

`overrideAttrs` changes the set given to `mkDerivation`: version, source, patches, flags. It takes a function from the old attributes to the changes.

```nix
pkgs.htop.overrideAttrs (old: {
  patches = (old.patches or [ ]) ++ [ ./htop-colors.patch ];
  configureFlags = (old.configureFlags or [ ]) ++ [ "--enable-sensors" ];
})
```

```nix
pkgs.tmux.overrideAttrs (old: rec {   # move to a newer version
  version = "3.6";
  src = pkgs.fetchFromGitHub {
    owner = "tmux"; repo = "tmux"; rev = version;
    hash = "sha256-...";
  };
})
```

| Want to change | Use |
| --- | --- |
| a dependency or feature flag in the argument list | `override` |
| version, source, patches, phases, flags | `overrideAttrs` |
| a Go module's vendor hash, a Rust cargo hash | `overrideAttrs` on the vendor part, or repackage |

### Overlays: change Nixpkgs for everyone

Overriding a package used in one place is easy. But if other packages depend on it, they still use the original. An **overlay** replaces it inside the package set itself, so every package that depends on it gets the new one.

An overlay is a function of two arguments, the final package set and the previous one:

```nix
# overlays/default.nix
final: prev: {
  htop = prev.htop.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ [ ./htop-colors.patch ];
  });
  tinytop = final.callPackage ../pkgs/tinytop/package.nix { };  # add a new package
}
```

Use **prev** for the thing you are changing (the version before your overlay), and **final** for everything else (the finished set, including your own additions). Mixing them up causes infinite recursion.

Apply it in NixOS:

```nix
nixpkgs.overlays = [ (import ./overlays) ];
environment.systemPackages = [ pkgs.htop pkgs.tinytop ];   # both are yours now
```

Or in a flake, export it and use it when importing Nixpkgs:

```nix
overlays.default = import ./overlays;
packages.x86_64-linux = let
  pkgs = import nixpkgs { system = "x86_64-linux"; overlays = [ self.overlays.default ]; };
in { inherit (pkgs) tinytop; };
```

::: {.pit t="Overlays cost build time"}
Overriding a library that many packages use (openssl, glibc, python3) changes the hash of everything that depends on it. None of it is in the binary cache any more, and your machine rebuilds hundreds of packages. Override leaf packages, or override only where you use the result.
:::

::: {.exer t="Exercises"}
1. Turn on the `withGui` argument of a package `pkgs.foo`.
2. In an overlay, why write `prev.htop.overrideAttrs` and not `final.htop.overrideAttrs`?

*Answers* 1 `pkgs.foo.override { withGui = true; }`. 2 `final.htop` is the result of this overlay, so defining `htop` in terms of itself loops forever. `prev.htop` is the version before.
:::

## Chapter 15. Home Manager

NixOS manages the system. **Home Manager** manages your user: packages just for you, and dotfiles for git, shells, editors and desktop apps, written in Nix. It works on NixOS and on any Linux or macOS with Nix.

### As a NixOS module

With the flake from Chapter 10, add one block to a host or common module:

```nix
home-manager = {
  useGlobalPkgs = true;     # use the system's pkgs and overlays
  useUserPackages = true;   # install into /etc/profiles, not ~/.nix-profile
  extraSpecialArgs = { inherit inputs; };
  users.ana = import ../home/ana.nix;
};
```

Now `nixos-rebuild switch` also builds Ana's home. Rollback covers both.

### A home file

```nix
# home/ana.nix
{ pkgs, ... }: {
  home.username = "ana";
  home.homeDirectory = "/home/ana";
  home.stateVersion = "26.05";          # same rule as system.stateVersion

  home.packages = with pkgs; [ ripgrep fd bat yt-dlp ];

  programs.git = {
    enable = true;
    settings.user = { name = "Ana"; email = "ana@example.org"; };
    settings.init.defaultBranch = "main";
  };
  programs.bash = {
    enable = true;
    shellAliases = { ll = "ls -l"; gs = "git status"; };
  };
  programs.direnv = { enable = true; nix-direnv.enable = true; };
  programs.starship.enable = true;

  home.file.".config/nvim/init.lua".source = ./nvim/init.lua;  # any dotfile
  home.sessionVariables.EDITOR = "nvim";
}
```

Home Manager writes the files as links into the store. Older releases spell the git name and email as `userName` and `userEmail`; the option search on the Home Manager site shows what your release expects.

### Standalone

On a machine where you are not root, or not on NixOS, install Home Manager alone and add a `homeConfigurations."ana"` output with `home-manager.lib.homeManagerConfiguration { pkgs = nixpkgs.legacyPackages.x86_64-linux; modules = [ ./home/ana.nix ]; }`. Apply with `home-manager switch --flake .#ana`.

::: {.pit t="Existing dotfiles block activation"}
If `~/.bashrc` already exists and is not a Home Manager link, activation stops with "Existing file ... is in the way". Move the old file away, or set `home-manager.backupFileExtension = "backup";` so Home Manager renames it for you.
:::

## Chapter 16. Secrets, VMs, containers and remote deploys

### Secrets stay out of the store

Every file in `/nix/store` is readable by every user, and anything in your Git repo ends up there. So a password must never be written in a `.nix` file. The pattern: commit only an **encrypted** file, and let a module decrypt it at boot into `/run`, readable only by the service that needs it.

```nix
# sops-nix: secrets.yaml is encrypted with the host's SSH key (age)
sops.defaultSopsFile = ./secrets.yaml;
sops.secrets."db-password".owner = "postgres";
services.myapp.passwordFile = config.sops.secrets."db-password".path;  # /run/secrets/db-password
```

```nix
# agenix: one .age file per secret
age.secrets.wifi.file = ../secrets/wifi.age;
networking.wireless.secretsFile = config.age.secrets.wifi.path;
```

Both are flake inputs that add a NixOS module. Look for options ending in `File` (`passwordFile`, `environmentFile`, `keyFile`): they take a path at runtime instead of a value at build time.

### Test VMs

```sh
$ nixos-rebuild build-vm --flake .#ember
$ ./result/bin/run-ember-vm      # QEMU window with your system, disk in ./ember.qcow2
```

The VM shares the configuration but not your disks, so it is the safe place to try a big change. Set `users.users.ana.initialPassword` (only used in the VM if no password file exists) so you can log in.

### NixOS containers

A full NixOS inside systemd-nspawn, sharing the host kernel and store:

```nix
containers.wiki = {
  autoStart = true;
  privateNetwork = true;
  hostAddress = "10.233.1.1";
  localAddress = "10.233.1.2";
  config = { pkgs, ... }: {
    services.nginx.enable = true;
    networking.firewall.allowedTCPPorts = [ 80 ];
    system.stateVersion = "26.05";
  };
};
```

Manage it with `nixos-container status wiki`, `nixos-container root-login wiki`.

### Docker images and OCI containers

Run images from a registry as systemd services:

```nix
virtualisation.oci-containers = {
  backend = "podman";
  containers.whoami = { image = "traefik/whoami:v1.10"; ports = [ "8080:80" ]; };
};
```

Or build an image with Nix, with no Dockerfile and no base image:

```nix
packages.x86_64-linux.image = pkgs.dockerTools.buildLayeredImage {
  name = "api";
  tag = "latest";
  contents = [ self.packages.x86_64-linux.default pkgs.cacert ];
  config.Cmd = [ "/bin/api" ];
};
```

`nix build .#image` gives a tarball; load it with `docker load < result`.

### Deploying to other machines

`nixos-rebuild --target-host` (Chapter 10) is enough for a few machines: it builds locally, copies the closure over SSH and activates it. For a fleet, tools like deploy-rs and colmena add parallel deploys and automatic rollback when a host stops answering. To install NixOS on a fresh server over SSH, nixos-anywhere with disko partitions the disk from a Nix file.

::: {.exer t="Exercises"}
1. Why is `services.myapp.password = "hunter2";` a bad idea, even in a private repo?
2. You want to try a new desktop without risking your laptop. What do you run?

*Answers* 1 The value lands in the world-readable store and in Git history. Use a `passwordFile` with sops-nix or agenix. 2 `nixos-rebuild build-vm --flake .#laptop` and run the VM.
:::
