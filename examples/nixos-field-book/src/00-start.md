# Start here: How to study Nix on paper

Nix looks strange until one idea clicks. This page gives you that idea and the habits that make the rest of the book easy.

## How to study Nix on paper

Every configuration here is shown in full, every command with its output, and every exercise has an answer. The examples use NixOS 26.05; change the number to the release you install.

**The one idea.** A package is the output of a pure function. Nix builds it from exact inputs (source code, compiler, libraries, build script) and stores the result in a folder whose name starts with a hash of all those inputs. Same inputs, same folder. Change anything, and you get a new folder next to the old one. Nothing is ever overwritten.

```sh
$ readlink -f $(which git)
/nix/store/9lsj6cx2vq2a1f0wb3kz8r5mhd4y7inp-git-2.47.1/bin/git
```

NixOS applies the same idea to the whole operating system. Your system is built from one configuration file into a store path, and "upgrading" means building a new path and pointing the machine at it. The old one stays, so you can always go back.

**The learning loop for each chapter**

1. Read the chapter once quickly, then again slowly, copying each example by hand. It forces you to notice every `;`, `=` and `{ }`.
2. Before reading a Terminal box, cover it and predict what the command prints.
3. Do the exercises. Answers sit under the dashed line: cover them with a card until you have tried.

### The three questions

Ask these of every snippet. Most confusion in Nix comes from losing track of one of them.

1. **Is this the language, a package, or a NixOS option?** `let ... in` is the language. `pkgs.git` is a package. `services.openssh.enable` is an option. They look alike but live in different worlds.
2. **What does this expression evaluate to?** Write the value in the margin.
3. **What ends up in the store, and what refers to it?**

::: {.tip t="Keep an option diary"}
Keep a notebook page called **Option diary**. Each time a chapter sets an option, write its full name, its type and what it does.
:::
