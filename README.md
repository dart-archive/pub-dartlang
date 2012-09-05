This is the server that will be used on `pub.dartlang.org` as the default
package repository for the Pub package manager.

For license information, please see LICENSE.

### Repository Structure

    pub_dartlang.py	The entry point for running the app.
    app.yaml		App Engine configuration.
    third_party/	External dependencies, included in the repo so that App
    			Engine will see them.
    handlers/		Code that handles HTTP requests.
    models/		Models for persisting data to the App Engine Datastore.
    views/		Mustache templates.

    test.py		The entry point for testing the app.
    tests/		Code for testing the app.

### Running the Server Locally

The server is written in Python and intended to run on Google App Engine. To run
it locally, perform the following steps:

  * Install the [App Engine SDK][].
  * Make sure the SDK is on your `$PATH`.
  * From the root directory of this repository, run:

        dev_appserver.py .

[app engine sdk]: https://developers.google.com/appengine/downloads

That's it. All the dependencies needed to run the app are included in the
repository so that App Engine can use them, so no further installation is
necessary.

### Running Tests

The tests have some external dependencies. Before you can run the tests,
perform the following steps once:

  * Install the [App Engine SDK][].
  * Make sure the SDK is on your `$PATH`.
  * Run:

        easy_install webtest
        easy_install beautifulsoup4

Once everything is installed, you can run the tests by running:

    ./test.py

### Modifying the CSS

The CSS files are generated from the source [Sass][] files using [Compass][].
To get ready to make changes, you'll need [Ruby][] and then:

[ruby]: http://ruby-lang.org
[sass]: http://sass-lang.com
[compass]: http://compass-style.org

 1. Ensure you have bundler installed:

        gem install bundler

 2. Run this to install bootstrap and the other dependencies:

        bundler install

Note that this is only needed on your development machine to iterate on the CSS.The deployed server just uses the pre-compiled CSS and only requires Python.

Once you have everything installed, to modify the styles:

 1. Edit the .scss files under `css/sass`.
 2. Regenerate the .css files from them (run this from the pub-dartlang root directory):

        bundle exec compass build css

You can also run `bundle exec compass watch` if you want a live refresh
experience. When you make changes to .scss files, make sure to regenerate and
check in the .css files with them.
