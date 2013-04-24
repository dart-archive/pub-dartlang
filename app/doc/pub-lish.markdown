---
title: "Command: Publish"
---

    $ pub publish [--dry-run] [--force] [--server <url>]

This command publishes your package on
[pub.dartlang.org](http://pub.dartlang.org) for anyone to download and depend
on. For example, if your package is named transmogrify, it will be listed on
`http://pub.dartlang.org/packages/transmogify`, and users can depend on it in
their pubspecs and get it via [pub install](pub-install.html) using something
like:

{% highlight dart %}
dependencies:
  transmogrify: ">= 1.0.0 < 2.0.0"
{% endhighlight %}

When publishing a package, it's important to follow the [pubspec
format](pubspec.html) and [package layout conventions](package-layout.html).
Some of these are required in order for others to be able to use your package.
Others are suggestions to help make it easier for users to understand and work
with your package. In both cases, pub will try to help you by pointing out what
changes will help make your package play nicer with the Dart ecosystem. There
are a few additional requirements for uploading a package:

* You must include a license file (named `LICENSE`, `COPYING`, or some
  variation) that contains an [open-source license](http://opensource.org/). We
  recommend the [BSD license](http://opensource.org/licenses/BSD-2-Clause),
  which is used by Dart itself. You must also have the legal right to
  redistribute anything that you upload as part of your package.

* Your package must be less than ten megabytes large after gzip compression. If
  it's too large, consider splitting it into multiple packages, or cutting down
  on the number of included resources or examples.

* Your package should only have hosted dependencies. Git dependencies are
  allowed but strongly discouraged; not everyone using Dart has Git installed,
  and Git dependencies don't support version resolution as well as hosted
  dependencies do.

Be aware that the email address associated with your Google account will be
displayed on [pub.dartlang.org](http://pub.dartlang.org) along with any packages
you upload.

## What files are published?

**All files** in your package will be included in the published package, with
the following exceptions:

* Any `packages` directories.
* Your package's [lockfile](glossary.html#lockfile).
* If you're using Git, any files ignored by your `.gitignore` file.
* If you aren't using Git, all "hidden" files (that is, files whose names begin
  with `.`).

If there are other files you don't want to include, be sure to delete them (or
add them to `.gitignore`) before running `pub publish`.

To be on the safe side, `pub publish` will list all files it's going to publish
for you to look over before it actually uploads your package.

## Options

### `--dry-run` or `-n`

With this, pub goes through the validation process but does not actually upload
the package. This is useful if you want to see if your package meets all of the
publishing requirements before you're ready to actually go public.

### `--force` or `-f`

With this, pub does not ask for confirmation before publishing. Normally, it
shows you the package contents and asks for you to confirm the upload.

If there are any errors in your package, it is not uploaded and this exits with
an error. If there are warnings, it *will* be uploaded. If you want to ensure
your package has no warnings before uploading, either don't use `--force`, or
use `--dry-run` first.

### `--server`

If you pass `--server` followed by a URL, it will attempt to publish the
package to that server. It assumes the server supports the same HTTP API that
[pub.dartlang.org][pubsite] uses.

This can be useful if you're running your own local package server for testing.
The main pub server is itself open source and available [here][pub repo].

[pubsite]: http://pub.dartlang.org
[pub repo]: https://github.com/dart-lang/pub-dartlang
