---
title: "Glossary"
---

### Dependency

Another package that your package relies on. If your package wants to import
code from some other package, that package must be a dependency. Dependencies
are specified in your package's [pubspec](pubspec.html).

### Entrypoint

"Entrypoint" is used to mean two things. In the general context of Dart, it is
a Dart library that is directly invoked by a Dart implementation. When you
reference a Dart library in a `<script>` tag or pass it as a command line
argument to the standalone Dart VM, that library is the entrypoint. In other
words, it's usually the `.dart` file that contains `main()`.

In the context of pub, an "entrypoint package" or "root package" is the root
of a dependency graph. It will usually be an application. When you run your app,
it's the entrypoint package. Every other package it depends on will not be an
entrypoint in that context.

A package can be an entrypoint in some contexts and not in others. Lets say your
app uses a library package A. When you run your app, A is not the entrypoint
package. However, if you go over to A and execute its unit tests, in that
context, it *is* the entrypoint since your app isn't involved.

### Immediate dependency

A [dependency](#dependency) that your package directly uses itself. The
dependencies you list in your pubspec are your package's immediate dependencies.
All other dependencies are [transitive dependencies](#transitive-dependency).

### Lockfile

A file named `pubspec.lock` that specifies the concrete versions and other
identifying information for every immediate and transitive dependency a package
relies on.

Unlike the pubspec, which only lists immediate dependencies and allows version
ranges, the lock file comprehensively pins down the entire dependency graph to
specific versions of packages. A lockfile ensures that you can recreate the
exact configuration of packages used by an application.

The lockfile is generated automatically for you by pub when you run
[`pub install`](pub-install.html) or [`pub update`](pub-update.html). If your
package is an application package, you will typically check this into source
control. For library packages, you usually won't.

### Source

A kind of place that pub can download and install packages from. A source isn't
a specific place like pub.dartlang.org or some specific Git URL. Each source
describes a general procedure for accessing a package in some way. For example,
"git" is one source. The git source knows how to download packages given a Git
URL. There are a few different
[supported sources](pubspec.html#dependency-sources).

### System cache

When pub installs a remote package, it downloads it into a single
"system cache" directory maintained by pub. When it generates a "packages"
directory for a package, that only contains symlinks to the real packages in
the system cache. On Mac and Linux, this directory defaults to `~/.pub-cache`.
On Windows, it goes in `AppData\Roaming\Pub\Cache`.

This means you only have to download a given version of a package once and can
then reuse it in as many packages as you would like. It also means you can
delete and regenerate your "packages" directory without having to access the
network.

### Transitive dependency

A dependency that your package indirectly uses because one of its dependencies
requires it. If your package depends on A, which in turn depends on B which
depends on C, then A is an [immediate dependency](#immediate-dependency) and B
and C are transitive ones.
