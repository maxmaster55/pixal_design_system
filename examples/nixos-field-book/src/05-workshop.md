# Part 5: Workshop

Real errors with their fixes, whole configurations you can copy, and a graded set of problems. This is where the earlier chapters turn into skill.

## Chapter 17. Troubleshooting clinic

Each case is an error almost every NixOS user meets in their first months. Read the code, predict the message, then compare your fix with the one given.

::: {.tip t="Read errors from the bottom up"}
Nix prints a long trace of where evaluation was when it failed. The last lines say **what** went wrong; the lines above say **where**, from the outside in. Add `--show-trace` to see the full trace when the short one hides the cause.
:::

::: {.case n="1" t="The option does not exist"}
```text
error: The option `services.ngnix' does not exist. Definition values:
       - In `/nix/store/...-source/hosts/ember/configuration.nix'
```
#### Diagnosis
A typo, an option from a newer release, or an option that was renamed or removed. Every option must be declared by some module.

#### Fix
Fix the spelling (`services.nginx`). If the name is right, check the option search for your release; renamed options usually print a warning with the new name for one release before they go.
:::

::: {.case n="2" t="infinite recursion encountered"}
```nix
{ config, lib, ... }: {
  imports = if config.services.nginx.enable
            then [ ./web.nix ] else [ ];
}
```
#### Diagnosis
To know `config`, NixOS must first collect every module, and that means reading `imports`. But here `imports` needs `config`. Neither can be computed first.

#### Fix
Always import, and decide inside the imported module with `lib.mkIf config.services.nginx.enable { ... }`. The same loop appears when an overlay defines `final.x` in terms of `final.x`: use `prev.x`.
:::

::: {.case n="3" t="hash mismatch in a fetcher"}
```text
error: hash mismatch in fixed-output derivation '/nix/store/...-source.drv':
         specified: sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
            got:    sha256-p3Kq0bJ1dZ6mYwq8xv2sJ0hTt9nF4cL7aE5uR1iWzGk=
```
#### Diagnosis
The downloaded content does not match the promised hash. When you are writing a new fetcher, this is expected.

#### Fix
Put `hash = lib.fakeHash;` (it gives the A's), build once, then paste the **got** value in. If a working build suddenly mismatches, upstream changed a tag or tarball: check before trusting the new hash. For Go and Rust, the same applies to `vendorHash` and `cargoHash`.
:::

::: {.case n="4" t="A new file is not found in a flake"}
```text
error: getting status of '/nix/store/...-source/modules/vpn.nix':
       No such file or directory
```
#### Diagnosis
The file exists on disk, but Git does not track it, so the flake copy in the store does not have it.

#### Fix
`git add modules/vpn.nix`. No commit needed. Nix prints a "Git tree is dirty" warning until you commit, which is harmless.
:::

::: {.case n="5" t="Unfree package refused"}
```text
error: Package 'steam-1.0.0.85' in /nix/store/...-source/pkgs/...
       has an unfree license ('unfreeRedistributable'), refusing to evaluate.
```
#### Fix
In NixOS: `nixpkgs.config.allowUnfree = true;`, or allow just this one with `allowUnfreePredicate` (Chapter 6). For a one-off `nix run`, use `NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#steam`. With `useGlobalPkgs`, Home Manager follows the system setting.
:::

::: {.case n="6" t="Conflicting definition values"}
```text
error: The option `networking.hostName' has conflicting definition values:
       - In `modules/common.nix': "box"
       - In `hosts/frost/configuration.nix': "frost"
```
#### Fix
Two modules set a single value at the same priority. Make the shared one a default: `networking.hostName = lib.mkDefault "box";`. When you do not own the other module, win with `lib.mkForce`.
:::

::: {.case n="7" t="A downloaded binary will not start"}
```sh
$ ./tool
Could not start dynamically linked executable: ./tool
NixOS cannot run dynamically linked executables intended for generic
linux environments out of the box.
```
#### Diagnosis
There is no `/lib64/ld-linux-x86-64.so.2` and no `/usr/lib` on NixOS.

#### Fix
Best: package it with `autoPatchelfHook` (Chapter 13). Quick: `programs.nix-ld.enable = true;` with the libraries it needs in `programs.nix-ld.libraries`. For games and closed apps, `steam-run ./tool` provides a typical Linux environment.
:::

::: {.case n="8" t="value is a function while a set was expected"}
```nix
environment.systemPackages = [ (import ./pkgs/tinytop.nix) ];
```
#### Diagnosis
`tinytop.nix` is a function `{ lib, stdenv, ... }: ...`. Importing it gives the function, not a package.

#### Fix
Call it with its arguments: `(pkgs.callPackage ./pkgs/tinytop.nix { })`. The reverse error, "attempt to call something which is not a function but a set", means you called a set: remove the extra argument.
:::

::: {.case n="9" t="cannot coerce a set to a string"}
```nix
script = "${pkgs.python3Packages} -m http.server";
```
#### Diagnosis
Only derivations, paths, strings and numbers can go into `${ }`. `pkgs.python3Packages` is a set of many packages.

#### Fix
Interpolate one package and a file in it: `"${pkgs.python3}/bin/python3 -m http.server"`. Better still, `lib.getExe pkgs.python3` gives the main program path.
:::

::: {.case n="10" t="undefined variable 'pkgs'"}
```nix
{ config, ... }: {
  environment.systemPackages = [ pkgs.git ];
}
```
#### Fix
The module never asked for `pkgs`. Add it to the arguments: `{ config, pkgs, ... }:`. The same goes for `lib`, and for `inputs` (which also needs `specialArgs`).
:::

::: {.case n="11" t="No space left on /boot"}
```text
OSError: [Errno 28] No space left on device: '/boot/EFI/nixos/...'
```
#### Diagnosis
Every generation with a different kernel keeps its kernel and initrd on the small boot partition.

#### Fix
Delete old generations and rebuild so the bootloader entries are rewritten: `sudo nix-collect-garbage --delete-older-than 7d` then `sudo nixos-rebuild boot`. Prevent it with `boot.loader.systemd-boot.configurationLimit = 10;`.
:::

::: {.case n="12" t="Read-only file system"}
```sh
$ sudo nano /etc/ssh/sshd_config      # save fails, or the change is lost
```
#### Diagnosis
The file is a link into the read-only store, generated from your options.

#### Fix
Change the option (`services.openssh.settings.X11Forwarding = true;`) and rebuild. Read the generated file with `cat` to check the result. For a program with no module, use `environment.etc."app/config.toml".text`.
:::

## Chapter 18. Recipe book: whole configs

Eight complete building blocks. Each is a module: put it in its own file and add it to `imports`, or paste it into `configuration.nix`. Replace names, addresses and keys with your own.

::: {.worked t="Recipe 1: a laptop desktop"}
```nix
{ pkgs, ... }: {
  networking.networkmanager.enable = true;
  services.displayManager.sddm.enable = true;
  services.desktopManager.plasma6.enable = true;
  services.pulseaudio.enable = false;
  security.rtkit.enable = true;
  services.pipewire = { enable = true; alsa.enable = true; pulse.enable = true; };
  hardware.bluetooth.enable = true;
  services.printing.enable = true;
  services.power-profiles-daemon.enable = true;
  programs.firefox.enable = true;
  fonts.packages = with pkgs; [ noto-fonts noto-fonts-color-emoji nerd-fonts.fira-code ];
  environment.systemPackages = with pkgs; [ vlc libreoffice-qt keepassxc ];
}
```
:::

::: {.worked t="Recipe 2: a home server, locked down"}
```nix
{ ... }: {
  services.openssh = {
    enable = true;
    settings = { PasswordAuthentication = false; PermitRootLogin = "no"; };
  };
  users.users.ana.openssh.authorizedKeys.keys = [ "ssh-ed25519 AAAAC3Nza... ana@laptop" ];
  services.fail2ban.enable = true;
  services.tailscale.enable = true;          # private network to your other devices
  services.jellyfin = { enable = true; openFirewall = true; };
  services.samba = {
    enable = true;
    openFirewall = true;
    settings.media = { path = "/data/media"; "read only" = "yes"; browseable = "yes"; };
  };
  nix.gc = { automatic = true; dates = "weekly"; options = "--delete-older-than 30d"; };
}
```
:::

::: {.worked t="Recipe 3: a website with HTTPS in 14 lines"}
```nix
services.nginx = {
  enable = true;
  recommendedTlsSettings = true;
  virtualHosts."notes.example.org" = {
    enableACME = true;   # get a certificate
    forceSSL = true;     # redirect http to https
    root = "/var/www/notes";
  };
};
security.acme = {
  acceptTerms = true;
  defaults.email = "admin@example.org";
};
networking.firewall.allowedTCPPorts = [ 80 443 ];
```
One rebuild installs nginx, writes its config, creates a systemd timer that renews the certificate and opens the firewall. To serve an app instead of files, replace `root` with `locations."/".proxyPass = "http://127.0.0.1:3000";`.
:::

::: {.worked t="Recipe 4: Docker or Podman host"}
```nix
{
  virtualisation.docker.enable = true;
  users.users.ana.extraGroups = [ "docker" ];
  # or, rootless and daemonless:
  # virtualisation.podman = { enable = true; dockerCompat = true; };
}
```
Membership of the `docker` group is equal to root access. Podman with `dockerCompat` gives you a `docker` command without that.
:::

::: {.worked t="Recipe 5: PostgreSQL for one app"}
```nix
{ pkgs, ... }: {
  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_16;
    ensureDatabases = [ "notes" ];
    ensureUsers = [ { name = "notes"; ensureDBOwnership = true; } ];
  };
  services.postgresqlBackup = { enable = true; databases = [ "notes" ]; };
}
```
A system user named `notes` can now connect over the local socket with no password. Pin the major version with `package`: upgrading PostgreSQL needs a data migration, so it never happens by surprise.
:::

::: {.worked t="Recipe 6: gaming"}
```nix
{
  nixpkgs.config.allowUnfree = true;
  hardware.graphics = { enable = true; enable32Bit = true; };
  programs.steam = { enable = true; remotePlay.openFirewall = true; };
  programs.gamemode.enable = true;
  # NVIDIA cards also need:
  # services.xserver.videoDrivers = [ "nvidia" ];
  # hardware.nvidia.open = true;
}
```
:::

::: {.worked t="Recipe 7: a WireGuard VPN server"}
```nix
{
  networking.firewall.allowedUDPPorts = [ 51820 ];
  networking.wireguard.interfaces.wg0 = {
    ips = [ "10.100.0.1/24" ];
    listenPort = 51820;
    privateKeyFile = "/var/lib/wireguard/private";  # create once, never in the store
    peers = [
      { publicKey = "xTIBA5rboUvnH4htodjb6e697QjLERt1NAB4mZqp8Dg=";  # the phone's key
        allowedIPs = [ "10.100.0.2/32" ]; }
    ];
  };
}
```
Create the key on the server with `wg genkey > /var/lib/wireguard/private` and get the public half with `wg pubkey < /var/lib/wireguard/private`.
:::

::: {.worked t="Recipe 8: a developer workstation"}
```nix
{ pkgs, ... }: {
  programs.direnv = { enable = true; nix-direnv.enable = true; };
  programs.nix-ld.enable = true;         # for editors' downloaded language servers
  programs.git.enable = true;
  virtualisation.podman.enable = true;
  environment.systemPackages = with pkgs; [ vscode gh jq httpie ];
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    trusted-users = [ "root" "@wheel" ];   # let wheel users add binary caches
    auto-optimise-store = true;
  };
  boot.binfmt.emulatedSystems = [ "aarch64-linux" ];  # build ARM packages on x86
}
```
`vscode` is unfree, so this host needs `allowUnfree` too. Project tools live in each project's dev shell (Chapter 11), not here.
:::

## Chapter 19. The exercise set

Twenty-five problems, from reading expressions to designing modules. Work on paper first; answers follow each group.

::: {.exer t="Level 1: read the language"}
1. `let x = 5; in x * 2 + 1`
2. `{ a = 1; } ? b`
3. `builtins.length [ (x: x) 1 [ 2 3 ] ]`
4. `let s = { a.b.c = 1; }; in s.a.b.c or 0`
5. `"n=${toString (1 + 2)}"`
6. `({ x, y ? 10 }: x + y) { x = 1; }`

*Answers* 1 `11`. 2 `false`. 3 `3`: a function, a number and a list. 4 `1`. 5 `"n=3"`. 6 `11`.
:::

::: {.exer t="Level 2: write expressions"}
7. A function that takes a list of numbers and returns their sum (use `builtins.foldl'`).
8. Turn `[ "a" "b" ]` into `{ a = true; b = true; }`.
9. `lib.mapAttrs` to add 1 to every value of `{ x = 1; y = 2; }`.
10. A list that holds `pkgs.git` always and `pkgs.gitui` only if `fancy` is true.

*Answers* 7 `builtins.foldl' (acc: n: acc + n) 0`. 8 `lib.genAttrs [ "a" "b" ] (_: true)`. 9 `lib.mapAttrs (name: v: v + 1) { x = 1; y = 2; }`. 10 `[ pkgs.git ] ++ lib.optional fancy pkgs.gitui`.
:::

::: {.exer t="Level 3: configure NixOS"}
11. Create user `sam` who may use sudo and Docker.
12. Without internet, how do you check whether the option `services.nextcloud.enable` exists on your release?
13. Mount the disk labelled `backup` at `/backup` with ext4.
14. Make SSH listen on port 2222 and open only that port.
15. Make the system clean the store every week and keep 14 days.

*Answers* 11 `users.users.sam = { isNormalUser = true; extraGroups = [ "wheel" "docker" ]; };` 12 `man configuration.nix` and search for it, or `nixos-option services.nextcloud.enable`. 13 `fileSystems."/backup" = { device = "/dev/disk/by-label/backup"; fsType = "ext4"; };` 14 `services.openssh.ports = [ 2222 ];` (the module opens its ports in the firewall by default, `services.openssh.openFirewall`). 15 `nix.gc = { automatic = true; dates = "weekly"; options = "--delete-older-than 14d"; };`
:::

::: {.exer t="Level 4: modules and priorities"}
16. A shared module sets `time.timeZone = "UTC";`. Host `frost` needs `"Africa/Cairo"`. What do you change so both can live together?
17. Write the `options` part of a module `my.motd` with `enable` and `text` (string, default `"Welcome"`).
18. Finish it: when enabled, set `users.motd` to the text.
19. Why does `config.my.motd.text` inside the same module see the user's value, not only the default?

*Answers* 16 Make the shared value `lib.mkDefault "UTC"`, so the host's plain value wins. 17 `options.my.motd = { enable = lib.mkEnableOption "a login message"; text = lib.mkOption { type = lib.types.str; default = "Welcome"; }; };` 18 `config = lib.mkIf config.my.motd.enable { users.motd = config.my.motd.text; };` 19 `config` is the final merge of all modules, so it already contains every definition, including the user's.
:::

::: {.exer t="Level 5: flakes"}
20. Write a minimal `flake.nix` whose only output is a NixOS host `box` from `./box.nix`.
21. Your flake has inputs `nixpkgs` and `agenix`, and agenix has its own nixpkgs. Make it use yours.
22. Pin `nixpkgs` to commit `9b6e1d2` without editing `flake.nix`, for one build only.
23. A dev shell for a project that needs Node 22 and pnpm, for x86_64 and aarch64 Linux.

*Answers* 20 `{ inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05"; outputs = { nixpkgs, ... }: { nixosConfigurations.box = nixpkgs.lib.nixosSystem { modules = [ ./box.nix ]; }; }; }` 21 `inputs.agenix.inputs.nixpkgs.follows = "nixpkgs";` 22 `nix build --override-input nixpkgs github:NixOS/nixpkgs/9b6e1d2`. 23 `devShells = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (s: { default = nixpkgs.legacyPackages.${s}.mkShell { packages = with nixpkgs.legacyPackages.${s}; [ nodejs_22 pnpm ]; }; });`
:::

::: {.exer t="Level 6: design"}
24. You have three servers that share 80 percent of their config and differ in services. Sketch the repo layout and `flake.nix`.
25. A teammate wants the newest `neovim` from unstable but everything else stable. Give two ways.

*Answers* 24 `modules/common.nix` for the shared part, one module per role (`web.nix`, `db.nix`), `hosts/<name>/` for hardware and host-only settings, and a `mkHost` helper in `flake.nix` that combines common, the host folder and its role modules (Chapter 10). 25 Add a `nixpkgs-unstable` input and use `inputs.nixpkgs-unstable.legacyPackages.${pkgs.stdenv.hostPlatform.system}.neovim` in `systemPackages`; or write an overlay `final: prev: { neovim = unstable.neovim; }` so every use of `pkgs.neovim` gets it.
:::
