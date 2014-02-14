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

  * Install the [App Engine SDK][] for Python.
  * Make sure the SDK is on your `$PATH`.<sup>1</sup>
  * Install required packages.<sup>2</sup>

        pip install beautifulsoup4 pycrypto webtest

  * From the root directory of this repository, run:

        dev_appserver.py app

[app engine sdk]: https://developers.google.com/appengine/downloads

  * Open your browser to <http://localhost:8080/> to see that it works.

  * To run tests:

        ./test.py

  * To publish packages to your local test server, visit <http://localhost:8080/admin>
    (sign in as administrator), go to the "Private Key" tab & enter any string
    into the private key field.

<sup>1</sup> This might have been done already if you allowed the Google App
             Engine launcher to add symbolic links to your `$PATH`.

<sup>2</sup> On installing packages:
* Beautiful Soup & WebTest are only required for running tests.
* Some Linux distributions come with PyCrypto installed by default.  Make sure
  at least version 2.6 installed.
* If using Mac and `pip` is not available, install [brew](http://brew.sh) and
  run `brew install python`.

### Deploying

See the docs on [branches and versions][].

[branches and versions]: https://github.com/dart-lang/pub-dartlang/wiki/Branches-and-Versions

### Modifying the CSS and Documentation

The CSS files are generated from the source [Sass][] files using [Compass][].
To get ready to make changes, you'll need [Ruby][] and [Python][]. Then:

[ruby]: http://ruby-lang.org
[python]: http://python.org
[sass]: http://sass-lang.com
[compass]: http://compass-style.org

 1. Ensure you have bundler installed:

        gem install bundler

 2. Run this to install the dependencies:

        bundle install

 3. Run this to install the latest version of Pygments for syntax highlighting:

        sudo pip install --upgrade pygments

Note that this is only needed on your development machine to iterate on the CSS. The deployed server just uses the pre-compiled CSS and only requires Python.

Once you have everything installed, to modify the styles:

 1. Run [Foreman][] to automatically regenerate the CSS files when any Sass
    files change:

        bundle exec foreman start

 1. Edit the `.scss` files under `css/sass`.

[foreman]: http://ddollar.github.com/foreman/

When you make changes to SCSS files, make sure to check in the generated CSS
files with them.
