---
title: "Pubspec Format"
---

1. [Name](#name)
1. [Version](#version)
1. [Description](#description)
1. [Author/Authors](#authorauthors)
1. [Homepage](#homepage)
1. [Documentation](#documentation)
1. [Dependencies](#dependencies)
1. [SDK constraints](#sdk-constraints)
{:.toc}

Every pub package needs some metadata so it can specify its
[dependencies](glossary.html#dependency). Pub packages that are shared with
others also need to provide some other information so users can discover them.
Pub stores this in a file named `pubspec.yaml`, which (naturally) is written in
the [YAML](http://www.yaml.org/) language.

At the top level are a series of fields. The currently supported ones are:

<dl class="dl-horizontal">
  <dt>Name</dt>
  <dd>Required for every package.</dd>
  <dt>Version</dt>
  <dd>Required for packages that will be hosted on pub.dartlang.org.</dd>
  <dt>Description</dt>
  <dd>Required for packages that will be hosted on pub.dartlang.org.</dd>
  <dt>Author/Authors</dt>
  <dd>Optional.</dd>
  <dt>Homepage</dt>
  <dd>Optional.</dd>
  <dt>Documentation</dt>
  <dd>Optional.</dd>
  <dt>Dependencies</dt>
  <dd>Can be omitted if your package has no dependencies.</dd>
  <dt>Dev dependencies</dt>
  <dd>Can be omitted if your package has no dev dependencies.</dd>
</dl>

All other fields will be ignored. A simple but complete pubspec looks something
like this:

{% highlight yaml %}
name: newtify
version: 1.2.3
description: >
  Have you been turned into a newt? Would you like to be? This
  package can help: it has all of the newt-transmogrification
  functionality you've been looking for.
author: Nathan Weizenbaum <nweiz@google.com>
homepage: http://newtify.dartlang.org
documentation: http://docs.newtify.com
dependencies:
  efts: '>=2.0.4 <3.0.0'
  transmogrify: '>=0.4.0'
dev_dependencies:
  unittest: '>=0.6.0'
{% endhighlight %}

## Name

Every package needs a name. When your stellar code gets props on
the world stage, this is what they'll be hollering. Also, it's how other
packages will refer to yours, and how it will appear here, should you publish
it.

It should be all lowercase, with underscores to separate words,
`just_like_this`. Stick with basic Latin letters and Arabic digits:
`[a-z0-9_]` and ensure that it's a valid Dart identifier (i.e. doesn't start
with digits and isn't a reserved word).

Try to pick a name that is clear, terse, and not already in use. A quick search
[here](/packages) to make sure nothing else is using your name can save you
heartache later.

## Version

Every package has a version. A version number is required to host your package
here, but can be omitted for local-only packages. If you omit it, your package
is implicitly versioned `0.0.0`.

No one really gets excited about versioning, but it's a necessary evil for
reusing code while letting it evolve quickly. A version number is three numbers
separated by dots, like `0.2.43`. It can also optionally have a build
(`+hotfix.oopsie`) or pre-release (`-alpha.12`) suffix.

Each time you publish your package, you will publish it at a specific version.
Once that's been done, consider it hermetically sealed: you can't touch it
anymore. To make more changes, you'll need a new version.

When you select a version, follow [semantic versioning][]. When you do, the
clouds will part and sunshine will pour into your soul. If you don't, prepare
yourself for hordes of angry users.

[semantic versioning]: http://semver.org

## Description

This is optional for your own personal packages, but if you intend to share
your package with the world (and you should because, let's be honest with
ourselves, it's a thing of beauty) you must provide a description. This should
be relatively short&mdash;a few sentences, maybe a whole paragraph&mdash;and
tells a casual reader what they might want to know about your package.

Think of the description as the sales pitch for your package. Users will see it
when they [browse for packages](/packages). It should be simple plain text:
no markdown or HTML. That's what your README is for.

## Author/Authors

You're encouraged to use these fields to describe the author(s) of your package
and provide contact information. `author` should be used if your package has a
single author, while `authors` should be used with a YAML list if more than one
person wrote the package. Each author can either be a single name (e.g. `Nathan
Weizenbaum`) or a name and an email address (e.g. `Nathan Weizenbaum
<nweiz@google.com>`). For example:

{% highlight yaml %}
authors:
- Nathan Weizenbaum <nweiz@google.com>
- Bob Nystrom <rnystrom@google.com>
{% endhighlight %}

If anyone uploads your package here, we will show this email address so make
sure you're OK with that.

## Homepage

This should be a URL pointing to the website for your package. For
[hosted packages](#hosted-packages), this URL will be linked from the
package's page. While this is technically optional *please do* provide one. It
helps users understand where your package is coming from. If nothing else, you
can always use the URL where you host the source code:
[GitHub](http://github.com), [code.google.com](http://code.google.com/),
whatever.

## Documentation

Some packages may have a site that hosts documentation separate from the main
homepage. If your package has that, you can also add a `documentation:` field
with that URL. If provided, a link to it will be shown on your package's page.

## Dependencies

<div class="learn-more">
  <a href="/doc/dependencies.html">
    Learn more about dependencies &rarr;
  </a>
</div>

Finally, the pubspec's *raison d'être*: [dependencies](glossary.html#dependency). Here,
you list each package that your package needs in order to work.

There are two separate sections. Dependencies under `dependencies:` are
"regular" dependencies. They are packages that anyone using your package will
also need. Dependencies under `dev_dependencies` are
[dev dependencies](glossary.html#dev-dependency). These are packages that are
only needed in the development of your package itself.

## SDK constraints

A package can indicate which versions of its dependencies it supports, but there
is also another implicit dependency all packages have: the Dart SDK itself.
Since the Dart platform evolves over time, a package may only work with certain
versions of it.

A package can specify that using an *SDK constraint*. This goes inside a
separate top-level "environment" field in the pubspec and uses the same
[version constraint](dependencies.html#version-constraints) syntax as
dependencies. For example, this constraint says that this package works with any
Dart SDK from 0.3.4 or later:

{% highlight yaml %}
environment:
  sdk: ">=0.3.4"
{% endhighlight %}

When you install a package that doesn't work with your installed Dart SDK, pub
will show you an error message and ask you to resolve it. You can usually fix
this by upgrading to the latest Dart SDK, or locking to an older version of that
dependency that does work with your SDK.

[pubsite]: http://pub.dartlang.org
[semantic versioning]: http://semver.org/
