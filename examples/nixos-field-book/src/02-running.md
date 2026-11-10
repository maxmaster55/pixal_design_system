# Part 2: Running NixOS

Install it, read your first configuration line by line, learn the module system that every option comes from, then the everyday settings and the rebuild loop.

## Chapter 4. Installing and your first configuration

Boot the NixOS installer from a USB stick. The graphical ISO has a point-and-click installer; the minimal ISO teaches you more, so here are its steps for a UEFI machine with one disk, `/dev/sda`. Run them as root (`sudo -i` first).

```sh
$ parted /dev/sda -- mklabel gpt
$ parted /dev/sda -- mkpart root ext4 512MB -8GB
$ parted /dev/sda -- mkpart swap linux-swap -8GB 100%
$ parted /dev/sda -- mkpart ESP fat32 1MB 512MB
$ parted /dev/sda -- set 3 esp on
$ mkfs.ext4 -L nixos /dev/sda1
$ mkswap -L swap /dev/sda2
$ mkfs.fat -F 32 -n boot /dev/sda3
$ mount /dev/disk/by-label/nixos /mnt
$ mkdir -p /mnt/boot
$ mount -o umask=077 /dev/disk/by-label/boot /mnt/boot
$ swapon /dev/sda2
$ nixos-generate-config --root /mnt
$ nano /mnt/etc/nixos/configuration.nix
$ nixos-install          # asks for a root password at the end
$ reboot
```

`nixos-generate-config` writes two files in `/mnt/etc/nixos/`:

| File | What it holds | Edit it? |
| --- | --- | --- |
| `hardware-configuration.nix` | detected disks, file systems, kernel modules, CPU type | rarely; regenerate it instead |
| `configuration.nix` | everything else: users, packages, services | yes, this is your system |

### Reading configuration.nix

Here is a trimmed first config. Read every line before you install.

```nix
{ config, pkgs, ... }:              # a module: a function of the system's arguments
{
  imports = [ ./hardware-configuration.nix ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "frost";
  networking.networkmanager.enable = true;

  time.timeZone = "Africa/Cairo";
  i18n.defaultLocale = "en_US.UTF-8";

  users.users.ana = {
    isNormalUser = true;
    extraGroups = [ "wheel" "networkmanager" ];  # wheel may use sudo
  };

  environment.systemPackages = with pkgs; [ git vim wget ];

  services.openssh.enable = true;

  system.stateVersion = "26.05";    # see the pitfall below
}
```

::: {.pit t="Never bump system.stateVersion to upgrade"}
`system.stateVersion` records which release first created this machine's data (database formats, default paths). It does **not** choose your NixOS version; your channel or flake input does. Leave it at the release you installed with, forever, unless you have read the release notes and migrated the data it protects.
:::

After the first boot, set your user's password with `passwd ana`. Never put a real password in the config: the store is world-readable.


::: {.exer t="Exercises"}
1. Which file should you edit to add a user, and which one describes your disks?
2. Your friend says: "To upgrade to 26.11, set stateVersion to 26.11." What is wrong?

*Answers* 1 `configuration.nix`; `hardware-configuration.nix`. 2 stateVersion does not select the release. Upgrade the channel or the flake input; leave stateVersion alone.
:::

## Chapter 5. The module system

Every NixOS option, from `networking.hostName` to `services.nginx`, comes from a **module**. Your `configuration.nix` is a module too. Understanding modules turns NixOS from magic into a tool.

### The shape of a module

A module is a function that returns a set with up to three keys:

```nix
{ config, pkgs, lib, ... }:   # arguments NixOS passes to every module
{
  imports = [ ./other.nix ];  # more modules to include
  options = { };              # options this module declares (rare in your own config)
  config = { };               # values this module sets
}
```

If a module has no `options`, you can drop the `config = { }` wrapper and write settings at the top level, which is what `configuration.nix` does.

NixOS collects **all** modules (about 2,000 from Nixpkgs plus yours), merges every `config` together, checks each value against its option's type, and only then builds the system. `config` in the arguments is the **final, merged** result. That is how one module can read what another set.

### Merging

When two modules set the same option, NixOS merges by type:

| Option type | Two definitions | Result |
| --- | --- | --- |
| list | `[ a ]` and `[ b ]` | `[ a b ]` (concatenated) |
| attribute set | `{ x = 1; }` and `{ y = 2; }` | `{ x = 1; y = 2; }` |
| lines (text) | two strings | joined with a newline |
| bool, str, int | `true` and `false` | error: conflicting definitions |

So each module can add its own packages to `environment.systemPackages`, and they all end up installed.

### Priorities

A conflict between single values is settled by priority. **Lower numbers win.**

| Written as | Priority | Use it for |
| --- | --- | --- |
| option's own default | 1500 | set by the option, not by you |
| `lib.mkDefault v` | 1000 | defaults in shared modules that hosts may override |
| `v` (plain) | 100 | normal settings |
| `lib.mkForce v` | 50 | override a value someone else set |

`lib.mkBefore` and `lib.mkAfter` do not change priority; they order list items and text.

### Conditions: mkIf and mkMerge

```nix
{ config, lib, pkgs, ... }: {
  config = lib.mkMerge [
    { environment.systemPackages = [ pkgs.git ]; }
    (lib.mkIf config.services.nginx.enable {
      networking.firewall.allowedTCPPorts = [ 80 443 ];
    })
  ];
}
```

`lib.mkIf cond set` is not an `if`: it pushes the condition into each option, so it can be evaluated after merging without causing loops. Use it whenever the condition reads `config`.

### Writing your own module

This is where NixOS becomes yours. A module that declares an option and acts on it:

```nix
# modules/backup.nix
{ config, lib, pkgs, ... }:
let cfg = config.my.backup; in {
  options.my.backup = {
    enable = lib.mkEnableOption "nightly home backups";
    target = lib.mkOption {
      type = lib.types.str;
      example = "/mnt/usb/backup";
      description = "Folder the backup is written to.";
    };
    paths = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ "/home" ];
      description = "Folders to back up.";
    };
  };
  config = lib.mkIf cfg.enable {
    systemd.services.my-backup = {
      description = "Nightly backup";
      startAt = "02:00";
      serviceConfig.Type = "oneshot";
      script = ''
        ${pkgs.rsync}/bin/rsync -a --delete ${lib.escapeShellArgs cfg.paths} ${cfg.target}
      '';
    };
  };
}
```

Use it from any host:

```nix
imports = [ ./modules/backup.nix ];
my.backup = { enable = true; target = "/mnt/usb/backup"; };
```

::: {.worked t="Who wins?"}
Module A: `networking.hostName = lib.mkDefault "box";`. Module B: `networking.hostName = "frost";`. B is priority 100, A is 1000, so the name is `frost`. If B had written `"frost"` and a third module wrote `"ice"`, both at 100, the build stops with "conflicting definition values". One of them needs `lib.mkForce`.
:::

::: {.exer t="Exercises"}
1. Two modules set `environment.systemPackages`. Do you get an error?
2. Why use `lib.mkIf` instead of `if ... then ... else { }` when the condition reads `config`?
3. Add an option `my.backup.user` of type string with default `"root"`.

*Answers* 1 No; lists are concatenated. 2 A plain `if` on `config` at the top of a module must be decided before NixOS knows the module's own definitions, which often causes infinite recursion; `mkIf` defers the decision into each value. 3 `user = lib.mkOption { type = lib.types.str; default = "root"; description = "User the backup runs as."; };` and `serviceConfig.User = cfg.user;`.
:::

## Chapter 6. Everyday configuration

The options most systems need, grouped by job. Search all options in the NixOS manual's appendix or with `man configuration.nix` on the machine.

### Users and shells

```nix
programs.zsh.enable = true;          # installs zsh and adds it to /etc/shells
users.users.ana = {
  isNormalUser = true;
  description = "Ana";
  extraGroups = [ "wheel" "networkmanager" "video" ];
  shell = pkgs.zsh;
  openssh.authorizedKeys.keys = [ "ssh-ed25519 AAAAC3Nza... ana@laptop" ];
};
users.mutableUsers = false;         # optional: users exist only if declared here
```

### Packages and unfree software

```nix
environment.systemPackages = with pkgs; [ firefox ripgrep fd tmux ];
nixpkgs.config.allowUnfree = true;  # or allow a list of names:
nixpkgs.config.allowUnfreePredicate = pkg:
  builtins.elem (lib.getName pkg) [ "steam" "discord" ];
```

Prefer `programs.<name>.enable` when it exists (for example `programs.firefox`, `programs.git`, `programs.steam`): it installs the package **and** sets up the config, groups and services it needs.

### Services

Most daemons are one switch plus settings. Each service declares its own options, so the shape differs a little.

```nix
services.openssh = {
  enable = true;
  settings.PasswordAuthentication = false;
  settings.PermitRootLogin = "no";
};
services.tailscale.enable = true;
services.fstrim.enable = true;       # weekly SSD trim
```

### Your own systemd units

```nix
systemd.services.hello-web = {
  description = "Tiny web server";
  wantedBy = [ "multi-user.target" ];   # start at boot
  after = [ "network.target" ];
  serviceConfig = {
    ExecStart = "${pkgs.python3}/bin/python3 -m http.server 8000";
    WorkingDirectory = "/srv/www";
    DynamicUser = true;                 # throwaway user, safer
    Restart = "on-failure";
  };
};
```

`startAt = "daily";` on a service makes NixOS create a matching timer for you.

### Networking and firewall

The firewall is **on by default** and blocks every incoming port except those you open.

```nix
networking = {
  hostName = "frost";
  networkmanager.enable = true;           # laptops; servers may use systemd-networkd
  firewall.allowedTCPPorts = [ 22 80 443 ];
  firewall.allowedUDPPorts = [ 51820 ];
  hosts."192.168.1.10" = [ "nas.home" ];  # extra /etc/hosts lines
};
```

### Boot, kernel and disks

```nix
boot.kernelPackages = pkgs.linuxPackages_latest;   # newer kernel than the default
boot.loader.systemd-boot.configurationLimit = 10;  # keep /boot from filling up
fileSystems."/data" = {
  device = "/dev/disk/by-label/data";
  fsType = "ext4";
  options = [ "noatime" ];
};
zramSwap.enable = true;                            # compressed swap in RAM
```

### Desktop, sound, printing

```nix
services.displayManager.sddm.enable = true;
services.desktopManager.plasma6.enable = true;
services.pulseaudio.enable = false;
security.rtkit.enable = true;
services.pipewire = { enable = true; alsa.enable = true; pulse.enable = true; };
services.printing.enable = true;
hardware.bluetooth.enable = true;
fonts.packages = with pkgs; [ noto-fonts nerd-fonts.jetbrains-mono ];
```

::: {.pit t="Editing files in /etc does not stick"}
Most of `/etc` is generated from your config and many files are links into the read-only store. Editing `/etc/hosts` by hand fails or is lost on the next rebuild. Find the option instead (`networking.hosts`), or use `environment.etc."myapp.conf".text = "...";` for files no option covers.
:::

::: {.exer t="Exercises"}
1. Open port 8080 for TCP.
2. Make a service that runs `/srv/clean.sh` every day.
3. Why is `programs.steam.enable` better than adding `pkgs.steam` to systemPackages?

*Answers* 1 `networking.firewall.allowedTCPPorts = [ 8080 ];` 2 `systemd.services.clean = { startAt = "daily"; serviceConfig.Type = "oneshot"; script = "${pkgs.bash}/bin/bash /srv/clean.sh"; };` (better: copy the script into the store with `./clean.sh`). 3 The module also enables 32-bit graphics libraries, udev rules for controllers and firewall settings Steam needs.
:::

## Chapter 7. Rebuilds, generations and rollback

You change the config, then ask NixOS to build it and switch to it. That is the whole workflow.

| Command | Builds | Activates now | Default at next boot |
| --- | --- | --- | --- |
| `nixos-rebuild switch` | yes | yes | yes |
| `nixos-rebuild boot` | yes | no | yes |
| `nixos-rebuild test` | yes | yes | no (gone after reboot) |
| `nixos-rebuild build` | yes, `./result` | no | no |
| `nixos-rebuild build-vm` | a VM, `./result/bin/run-*-vm` | no | no |
| `nixos-rebuild dry-build` | shows what would build | no | no |

Use `test` for risky changes such as network or firewall rules on a remote machine: if you lock yourself out, a reboot brings the old system back. Use `boot` for kernel or init changes you want to apply cleanly on the next start.

::: {.term t="A rebuild, step by step"}
```sh
$ sudo nixos-rebuild switch
building the system configuration...
these 3 derivations will be built:
  /nix/store/...-etc-ssh-sshd_config.drv
  /nix/store/...-etc.drv
  /nix/store/...-nixos-system-frost-26.05.20261030.9b6e1d2.drv
activating the configuration...
setting up /etc...
restarting the following units: sshd.service
Done. The new configuration is /nix/store/...-nixos-system-frost-26.05...
```
:::

Activation compares the old and new systems and restarts only the units whose files changed.

### Generations and rollback

```sh
$ nixos-rebuild list-generations
Generation  Build-date           NixOS version            Kernel  Current
42          2026-11-04 21:12:07  26.05.20261030.9b6e1d2   6.12.55 True
41          2026-10-28 09:40:51  26.05.20261021.3f0a8ac   6.12.53 False
$ sudo nixos-rebuild switch --rollback       # back to 41
```

Every generation also gets a boot menu entry, so a system that does not boot is fixed by choosing the line below.

### Updating the system

Without flakes, the version of Nixpkgs comes from a **channel**:

```sh
$ sudo nix-channel --list
nixos https://nixos.org/channels/nixos-26.05
$ sudo nixos-rebuild switch --upgrade      # update channel, then rebuild
```

Moving to a new release means pointing the channel at the new name (`nix-channel --add https://nixos.org/channels/nixos-26.11 nixos`) and rebuilding. With flakes you change an input URL instead; Part 3 shows how, and why most people now prefer it.

### Keeping the store clean

```nix
nix.gc = { automatic = true; dates = "weekly"; options = "--delete-older-than 14d"; };
nix.optimise.automatic = true;
boot.loader.systemd-boot.configurationLimit = 10;
```

::: {.exer t="Exercises"}
1. You are changing firewall rules over SSH. Which rebuild command protects you?
2. After a bad switch the system still boots but Wi-Fi is broken. Name two ways back.

*Answers* 1 `nixos-rebuild test`: if you are locked out, reboot and the old generation is still the default. 2 `sudo nixos-rebuild switch --rollback`, or reboot and pick the previous generation in the boot menu.
:::
