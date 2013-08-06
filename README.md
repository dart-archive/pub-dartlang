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
  * Make sure the SDK is on your `$PATH`<sup>1</sup>.
  * Install [PyCrypto][pycrypto] and [WebTest][webtest]<sup>2</sup>.

        pip install beautifulsoup4 pycrypto webtest

  * From the root directory of this repository, run:

        dev_appserver.py app

[app engine sdk]: https://developers.google.com/appengine/downloads
[pycrypto]: https://www.dlitz.net/software/pycrypto/
[webtest]: https://webtest.readthedocs.org/en/latest/

  * Open your browser to <http://localhost:8080/> to see that it works.

  * To run tests:

        ./test.py

In order to publish packages to your local test server, you must setup a
_private key_. Visit <http://localhost:8080/admin> (sign in as administrator)
and enter whatever you like into the private key field.

<sup>1</sup>This might have been done already if you allowed the Google App
            Engine launcher to add symbolic links to your `$PATH`.

<sup>2</sup>WebTest is only required for running tests.  **Linux:** Some Linux 
            distributions come with PyCrypto installed by default.  Make sure
            you have at least version 2.6 installed. **Mac:** If pip is not 
            available, try [brew](http://brew.sh) and `brew install python`.

### Deploying

See the docs on [branches and versions][].

[branches and versions]: https://github.com/dart-lang/pub-dartlang/wiki/Branches-and-Versions

### Modifying the CSS and Documentation

The CSS files are generated from the source [Sass][] files using [Compass][].
The HTML documentation files are generated from the source [Markdown][] using
[Jekyll][]. To get ready to make changes, you'll need [Ruby][] and [Python][].
Then:

[ruby]: http://ruby-lang.org
[python]: http://python.org
[sass]: http://sass-lang.com
[compass]: http://compass-style.org
[markdown]: http://daringfireball.net/projects/markdown/
[jekyll]: http://jekyllrb.com/

 1. Ensure you have bundler installed:

        gem install bundler

 2. Run this to install the dependencies:

        bundle install

 3. Run this to install the latest version of Pygments for syntax highlighting:

        sudo pip install --upgrade pygments

Note that this is only needed on your development machine to iterate on the CSS
and documentation. The deployed server just uses the pre-compiled CSS and HTML
and only requires Python.

Once you have everything installed, to modify the styles and documentation:

 1. Run [Foreman][] to automatically regenerate the CSS and HTML files when any
    Sass or Markdown files change:

        bundle exec foreman start

 1. Edit the `.scss` files under `css/sass` and the `.markdown` files under
    `doc`.

[foreman]: http://ddollar.github.com/foreman/

When you make changes to SCSS or Markdown files, make sure to check in the
generated CSS or HTML files with them.
