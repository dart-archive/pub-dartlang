---
title: "Dependencies"
---

1. [Sources](#sources)
    1. [Hosted packages](#hosted-packages)
    1. [Git packages](#git-packages)
    1. [Path packages](#path-packages)
1. [Version constraints](#version-constraints)
1. [Dev dependencies](#dev-dependencies)
{:.toc}

Dependencies are one of pub's core concepts. A dependency is another package
that your package needs in order to work. Dependencies are specified in your
[pubspec](pubspec.html). You only list
[immediate dependencies](glossary.html#immediate-dependency)&mdash;the stuff
your package uses directly. Pub handles
[transitive dependencies](glossary.html#transitive-dependency) for you.

For each dependency, you specify the *name* of the package you depend on. For
[library packages](glossary.html#library-package), you specify the *range of
versions* of that package that you allow. You may also specify the
[*source*](glossary.html#source) which tells pub how the package can be located,
and any additional *description* that the source needs to find the package.

There are two different ways to specify dependencies based on what data you want
to provide. The shortest way is to just specify a name:

{% highlight yaml %}
dependencies:
  transmogrify:
{% endhighlight %}

This creates a dependency on `transmogrify`that  allows any version, and looks
it up using the default source, which is this site itself. To limit the
dependency to a range of versions, you can provide a *version constraint*:

{% highlight yaml %}
dependencies:
  transmogrify: '>=1.0.0 <2.0.0'
{% endhighlight %}

This creates a dependency on `transmogrify` using the default source and
allowing any version from `1.0.0` to `2.0.0` (but not including `2.0.0`). See
[below](#version-constraints) for details on the version constraint syntax.

If you want to specify a source, the syntax looks a bit different:

{% highlight yaml %}
dependencies:
  transmogrify:
    hosted:
      name: transmogrify
      url: http://some-package-server.com
{% endhighlight %}

This depends on the `transmogrify` package using the `hosted` source.
Everything under the source key (here, just a map with a `url:` key) is the
description that gets passed to the source. Each source has its own description
format, detailed below.

You can also provide a version constraint:

{% highlight yaml %}
dependencies:
  transmogrify:
    hosted:
      name: transmogrify
      url: http://some-package-server.com
    version: '>=1.0.0 <2.0.0'
{% endhighlight %}

This long form is used when you don't use the default source or when you have a
complex description you need to specify. But in most cases, you'll just use the
simple "name: version" form.

## Dependency sources

Here are the different sources pub can use to locate packages, and the
descriptions they allow:

### Hosted packages

A *hosted* package is one that can be downloaded from this site (or another
HTTP server that speaks the same API). Most of your dependencies will be of
this form. They look like this:

{% highlight yaml %}
dependencies:
  transmogrify: '>=0.4.0 <1.0.0'
{% endhighlight %}

Here, you're saying your package depends on a hosted package named
"transmogrify" and you'll work with any version from 0.4.0 to 1.0.0 (but not
1.0.0 itself).

If you want to use your own package server, you can use a description that
specifies its URL:

{% highlight yaml %}
dependencies:
  transmogrify:
    hosted:
      name: transmogrify
      url: http://your-package-server.com
    version: '>=0.4.0 <1.0.0'
{% endhighlight %}

### Git packages

Sometimes you live on the bleeding edge and you need to use stuff that hasn't
been formally released yet. Maybe your package itself is still in development
and is using other packages that are being developed at the same time. To make
that easier, you can depend directly on a package stored in a [Git][]
repository.

[git]: http://git-scm.com/

{% highlight yaml %}
dependencies:
  kittens:
    git: git://github.com/munificent/kittens.git
{% endhighlight %}

The `git` here says this package is found using Git, and the URL after that is
the Git URL that can be used to clone the package. Pub assumes that the package
is in the root of the git repository.

If you want to depend on a specific commit, branch, or tag, you can also
provide a `ref` argument:

{% highlight yaml %}
dependencies:
  kittens:
    git:
      url: git://github.com/munificent/kittens.git
      ref: some-branch
{% endhighlight %}

The ref can be anything that Git allows to [identify a commit][commit].

[commit]: http://www.kernel.org/pub/software/scm/git/docs/user-manual.html#naming-commits

### Path packages

Sometimes you find yourself working on multiple related packages at the same
time. Maybe you are hacking on a framework while building an app that uses it.
In those cases, during development you really want to depend on the "live"
version of that package on your local file system. That way changes in one
package are instantly picked up by the one that depends on it.

To handle that, pub supports *path dependencies*.

{% highlight yaml %}
dependencies:
  transmogrify:
    path: /Users/me/transmogrify
{% endhighlight %}

This says the root directory for `transmogrify` is `/Users/me/transmogrify`.
When you use this, pub will generate a symlink directly to the `lib` directory
of the referenced package directory. Any changes you make to the dependent
package will be seen immediately. You don't need to run pub every time you
change the dependent package.

Relative paths are allowed and are considered relative to the directory
containing your pubspec.

Path dependencies are useful for local development, but do not play nice with
sharing code with the outside world. It's not like everyone can get to
your file system, after all. Because of this, you cannot upload a package to
[pub.dartlang.org][pubsite] if it has any path dependencies in its pubspec.

Instead, the typical workflow is:

1. Edit your pubspec locally to use a path dependency.
2. Hack on the main package and the package it depends on.
3. Once they're both in a happy place, publish the dependent package.
4. Then change your pubspec to point to the now hosted version of its dependent.
5. Now you can publish your main package too if you want.

## Version constraints

If your package is an application, you don't usually need to specify [version
constraints](glossary.html#version-constraint) for your dependencies. You will
typically want to use the latest versions of the dependencies when you first
create your app. Then you'll create and check in a
[lockfile](glossary.html#lockfile) that pins your dependencies to those specific
versions. Specifying version constraints in your pubspec then is usually
redundant (though you can do it if you want).

For a [library package](glossary.html#library-package) that you want users to
reuse, though, it is important to specify version constraints. That lets people
using your package know which versions of its dependencies they can rely on to
be compatible with your library. Your goal is to allow a range of versions as
wide as possible to give your users flexibility. But it should be narrow enough
to exclude versions that you know don't work or haven't been tested.

The Dart community uses [semantic versioning][], which helps you know which
versions should work. If you know that your package works fine with `1.2.3` of
some dependency, then semantic versioning tells you that it should work (at
least) up to `2.0.0`.

A version constraint is a series of:

<dl class="dl-horizontal">
  <dt><code>any</code></dt>
  <dd>The string "any" allows any version. This is equivalent to an empty
    version constraint, but is more explicit.</dd>

  <dt><code>1.2.3</code></dt>
  <dd>A concrete version number pins the dependency to only allow that
    <em>exact</em> version. Avoid using this when you can because it can cause
    version lock for your users and make it hard for them to use your package
    along with other packages that also depend on it.</dd>

  <dt><code>&gt;=1.2.3</code></dt>
  <dd>Allows the given version or any greater one. You'll typically use this.
    </dd>

  <dt><code>&gt;1.2.3</code></dt>
  <dd>Allows any version greater than the specified one but <em>not</em> that
    version itself.</dd>

  <dt><code>&lt;=1.2.3</code></dt>
  <dd>Allows any version lower than or equal to the specified one. You
    <em>won't</em> typically use this.</dd>

  <dt><code>&lt;1.2.3</code></dt>
  <dd>Allows any version lower than the specified one but <em>not</em> that
    version itself. This is what you'll usually use because it lets you specify
    the upper version that you know does <em>not</em> work with your package
    (because it's the first version to introduce some breaking change).</dd>
</dl>

You can specify version parts as you want, and their ranges will be intersected
together. For example, `>=1.2.3 <2.0.0` allows any version from `1.2.3` to
`2.0.0` excluding `2.0.0` itself.

<aside class="alert alert-warning">

Note that <code>&gt;</code> is also valid YAML syntax so you will want to quote
the version string (like <code>'&lt;=1.2.3 &gt;2.0.0'</code>) if the version
constraint starts with that.

</aside>

## Dev dependencies

Pub supports two flavors of dependencies: regular dependencies and *dev
dependencies.* Dev dependencies differ from regular dependencies in that *dev
dependencies of packages you depend on are ignored*. That's a mouthful, so
here's a motivating example:

Say the `transmogrify` package uses the `unittest` package in its tests and only
in its tests. If someone just wants to use `transmogrify`&mdash;import its
libraries&mdash;it doesn't actually need `unittest`. In this case, it specifies
`unittest` as a dev dependency. Its pubspec will have something like:

{% highlight yaml %}
dev_dependencies:
  unittest: '>=0.5.0'
{% endhighlight %}

Pub gets every package your package package depends on, and everything *those*
packages depend on, transitively. It also gets your package's dev dependencies.
But it *ignores* the dev dependencies of any dependent packages. Pub only gets
*your* package's dev dependencies. So when your package depends on
`transmogrify` it will get `transmogrify` but not `unittest`.

The rule for deciding between a regular or dev dependency is pretty simple. If
the dependency is imported from something in your `lib` directory, it needs to
be a regular dependency. If it's only imported from `test`, `example`, etc. it
can and should be a dev dependency.

Using dev dependencies makes dependency graphs smaller. That makes pub run
faster, and makes it easier to find a set of package versions that satisfy all
constraints. Use them when you can and your users will thank you.

[pubsite]: http://pub.dartlang.org
[semantic versioning]: http://semver.org/
