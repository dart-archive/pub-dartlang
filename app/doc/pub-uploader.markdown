---
title: "Command: Publish"
---

    $ pub uploader [options] {add/remove} <email>

This command allows [uploaders](glossary.html#uploader) of a package
on [pub.dartlang.org](http://pub.dartlang.org) to add or remove other
uploaders for that package. It has two sub-commands, `add` and
`remove`, that both take the email address of the person to add as an
uploader. For example:

    ~/code/transmogrify$ pub uploader add nweiz@google.com
    'nweiz@google.com' added as an uploader for package 'transmogrify'.

    ~/code/transmogrify$ pub uploader remove nweiz@google.com
    'nweiz@google.com' is no longer an uploader for package 'transmogrify'.

By default, the package in the current working directory will have its
uploaders modified. You can also pass the `--package` flag to choose a
package manually. For example:

    $ pub uploader --package=transmogrify add nweiz@google.com
    'nweiz@google.com' added as an uploader for package 'transmogrify'.

It's important to note that uploaders are identified by their Google
accounts, so you'll need to provide a Gmail or Google Apps email
address for any new uploaders.
