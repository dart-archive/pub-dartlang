---
title: "Getting Started"
---

1. [Installing and configuring pub](#installing-and-configuring-pub)
1. [Creating a package](#creating-a-package)
1. [Adding a dependency](#adding-a-dependency)
1. [Installing dependencies](#installing-dependencies)
1. [Importing code from a dependency](#importing-code-from-a-dependency)
1. [Updating a dependency](#updating-a-dependency)
1. [Publishing a package](#publishing-a-package)
{:.toc}

*Pub* is a package manager for Dart. It helps you reuse existing Dart code
and bundle your Dart apps and libraries so that you can reuse and share them
with other people. Pub handles versioning and dependency management so that you
can ensure that your app runs on other machines exactly the same as it does on
yours.

To **find** a package that's on pub.dartlang.org,
use the Search box at the top right of this page.

To **use** a package that's on pub.dartlang.org:

1. Create a top-level `pubspec.yaml` file for your app
   (if one doesn't already exist)
   and list the package as a dependency:

        name: my_app
        dependencies:
          js: 0.0.13
   
1. Run `pub install`, either on the command line
   or through the Dart Editor menu: Tools > Pub Install.

1. Import the package in your app:
   
    {% highlight dart %}
import 'package:js/js.dart';
{% endhighlight %}

For details and pointers to more documentation, read on.

## Installing and configuring pub

Pub is in the [Dart SDK](http://www.dartlang.org/docs/sdk/),
which you can download by itself or as part of
[Dart Editor](http://www.dartlang.org/docs/editor/).
You can use pub through
[Dart Editor](http://www.dartlang.org/docs/editor/), or through the
`pub` command-line app, which lives inside the `bin` directory of the Dart SDK.

To use pub and other tools on the command line,
you might want to add the SDK's `bin` directory to your system path.
For example, on Mac and Linux:

    export PATH=$PATH:<path to sdk>/bin

Here, `<path to sdk>` is the absolute path
to the main directory of the SDK. For example,
if you install Dart Editor in
`/home/me/dart`, then add this to your PATH:

    /home/me/dart/dart-sdk/bin

On Windows, you can set the system PATH environment variable through the
Control Panel. A quick
[search](https://www.google.com/search?q=windows+set+environment+variable)
should find the instructions for your version of Windows.

## Creating a package

<div class="learn-more">
  <a href="/doc/package-layout.html">
    Learn more about packages &rarr;
  </a>
</div>

A **package** in pub is a directory that contains Dart code and any other stuff
that goes along with it like resources, tests, and docs. Frameworks and
reusable libraries are obviously packages, but applications are too. If your
app wants to use pub packages, it needs to be a package too.

While everything is a package in pub, there are two flavors of packages that are
used slightly differently in practice. A [**library
package**](glossary.html#library-package) is a package that is intended to be
reused by other packages. It will usually have code that other packages import,
and it will likely be hosted somewhere that people can get to. An [**application
package**](glossary.html#application-package) only *consumes* packages but
doesn't itself get reused. In other words, library packages will be used as
dependencies, but application packages won't.

In most cases, there's no difference between the two and we'll just say
"package". In the few places where it does matter, we'll specify "library
package" or "application package".

<div class="learn-more">
  <a href="/doc/pubspec.html">
    Learn more about pubspecs &rarr;
  </a>
</div>

To turn your app into an application package so it can use other packages, you
just need to give it a **pubspec**. This file is written using the
[YAML language](http://yaml.org) and is named `pubspec.yaml`. The simplest
possible pubspec just contains the name of the package. Save the pubspec file as
`pubspec.yaml` in the root directory of your app.

Behold, the simplest possible `pubspec.yaml`:

{% highlight yaml %}
name: my_app
{% endhighlight %}

Now `my_app` is a pub package!

## Adding a dependency

<div class="learn-more">
  <a href="/doc/pubspec.html#dependencies">
    Learn more about dependencies &rarr;
  </a>
</div>

One of pub's main jobs is managing **dependencies**. A dependency is just
another package that your package relies on. If your app is using some
transformation library called "transmogrify", then your app package will depend
on the `transmogrify` package.

You specify your package's dependencies in the pubspec file immediately after
your package name. For example:

{% highlight yaml %}
name: my_app
dependencies:
  transmogrify:
{% endhighlight %}

Here, we are declaring a dependency on the (fictional) `transmogrify` package.

## Installing dependencies

<div class="learn-more">
  <a href="/doc/pub-install.html">
    Learn more about <tt>pub install</tt> &rarr;
  </a>
</div>

Once you've declared a dependency, you then tell pub to install it for you. If
you're using the Editor, select "Pub Install" from the "Tools" menu. If you're
rocking the command line, do:

    $ cd path/to/your_app
    $ pub install

<aside class="alert alert-warning">
Today, this command must be run from the directory containing
<tt>pubspec.yaml</tt>. In the future, you will be able to run it from any
sub-directory of the package.
</aside>

When you do this, pub will create a `packages` directory in the same directory
as `pubspec.yaml`. In there, it will download and install each package that
your package depends on (these are called your **immediate dependencies**). It
will also look at all of those packages and install everything *they* depend
on, recursively (these are your **transitive dependencies**).

When this is done, you will have a `packages` directory that contains every
single package your program needs in order to run.

## Importing code from a dependency

Now that you have a dependency wired up, you want to be able to use code from
it. To access a library in a another package, you will import it using the
`package:` scheme:

{% highlight dart %}
import 'package:transmogrify/transmogrify.dart';
{% endhighlight %}

This looks inside the `transmogrify` package for a top-level file named
`transmogrify.dart`. Most packages just define a single entrypoint whose name
is the same as the name of the package. Check the documentation for the package
to see if it exposes anything different for you to import.

<aside class="alert alert-info">
This works by looking inside the generated <tt>packages</tt> directory. If you
get an error, the directory may be out of date. Fix it by running
<tt>pub install</tt> whenever you change your pubspec.
</aside>

You can also use this style to import libraries from within your own package.
For example, let's say your package is laid out like:

    transmogrify/
      lib/
        transmogrify.dart
        parser.dart
      test/
        parser/
          parser_test.dart

The `parser_test` file *could* import `parser.dart` like this:

{% highlight dart %}
import '../../lib/parser.dart';
{% endhighlight %}

But that's a pretty nasty relative path. If `parser_test.dart` is ever moved
up or down a directory, that path will break and you'll have to fix the code.
Instead, you can do:

{% highlight dart %}
import 'package:transmogrify/parser.dart';
{% endhighlight %}

This way, the import can always get to `parser.dart` regardless of where the
importing file is.

<!-- TODO(rnystrom): Enable this when that doc exists.
<div class="learn-more">
  <a href="/doc/package-scheme.html">
  Learn more about the <tt>package:</tt> scheme
    <i class="icon-hand-right icon-white">&nbsp;</i>
  </a>
</div>
-->

## Updating a dependency

<div class="learn-more">
  <a href="/doc/pub-update.html">
  Learn more about <tt>pub update</tt> &rarr;
  </a>
</div>

The first time you install a new dependency for your package, pub will download
the latest version of it that's compatible with your other dependencies. It
then locks your package to *always* use that version by creating a **lockfile**.
This is a file named `pubspec.lock` that pub creates and stores next to your
pubspec. It lists the specific versions of each dependency (immediate and
transitive) that your package uses.

If this is an application package, you will check this file into source control.
That way, everyone hacking on your app ensures they are using the same versions
of all of the packages. This also makes sure you use the same versions of stuff
when you deploy your app to production.

When you are ready to upgrade your dependencies to the latest versions, do:

    $ pub update

This tells pub to regenerate the lockfile using the newest available versions of
your package's dependencies. If you only want to update a specific dependency,
you can specify that too:

    $ pub update transmogrify

This updates `transmogrify` to the latest version but leaves everything else the
same.

## Publishing a package

<div class="learn-more">
  <a href="/doc/pub-lish.html">
  Learn more about <tt>pub publish</tt> &rarr;
  </a>
</div>

Pub isn't just for using other people's packages. It also allows you to share
your packages with the world. Once you've written some useful code and you want
everyone else to be able to use it, just run:

    $ pub publish

Pub will check to make sure that your package follows the [pubspec
format](pubspec.html) and [package layout conventions](package-layout.html), and
then upload your package to [pub.dartlang.org](http://pub.dartlang.org). Then
any Pub user will be able to download it or depend on it in their pubspecs. For
example, if you just published version 1.0.0 of a package named `transmogrify`,
then they can write:

{% highlight yaml %}
dependencies:
  transmogrify: ">= 1.0.0 < 2.0.0"
{% endhighlight %}

Keep in mind that publishing is forever. As soon as you publish your awesome
package, users will be able to depend on it. Once they start doing that,
removing the package would break theirs. To avoid that, pub strongly discourages
deleting packages. You can always upload new versions of your package, but old
ones will continue to be available for users that aren't ready to upgrade yet.
