This is the server that will be used on `pub.dartlang.org` as the default
package repository for the Pub package manager.

For license information, please see [LICENSE](LICENSE).

## Repository structure

    |-- app/                    The app engine app.
    |   |-- doc/                Documentation and articles.
    |   |-- handlers/           Core web server code.
    |       |-- ...
    |   |-- models/             Models for persisting data to the datastore.
    |       |-- ...
    |   |-- static/             Static assets.
    |       |-- img/
    |           |-- ...
    |       |-- js/
    |           |-- ...
    |       |-- favicon.ico
    |       |-- style.css       Generated stylesheet. Modify /css/sass/style.scss instead.
    |   |-- views/              Mustache templates.
    |       |-- doc/            Generated HTML. Modify /app/doc/ files instead.
    |           |-- ...
    |       |-- ...
    |   |-- app.yaml            AppEngine configuration.
    |   |-- appengine_config.py Python module configuration.
    |   |-- pub_dartlang.py     Entrypoint for app. Use dev_appserver.py to run.
    |   |-- ...
    |
    |-- css/
    |   |-- sass/
    |       |-- _syntax.scss    Dart language syntax styles.
    |       |-- style.scss      Main stylesheet.
    |   |-- config.rb           Compass configuration.
    |
    |-- test/                   Tests for app functionality.
    |   |-- ...
    |
    |-- third_party/            External dependencies to be include in the app.
    |   |-- ...
    |
    |-- _config.yml             Jekyll configuration.
    |-- Procfile                Process to be run with Foreman.
    |-- test.py                 Tests the app.
    |-- ...

## Running the server locally

**tl;dr:** Run the app with ```dev_appserver.py app```.

### Prerequisites
The server is written in Python and intended to run on Google App Engine. To run
it locally, perform the following steps:

  1. Install the [App Engine SDK][] for Python.
  * Make sure the SDK is on your `$PATH`.<sup>1</sup>
  * Install required packages.<sup>2</sup>

        pip install beautifulsoup4 pycrypto webtest

[app engine sdk]: https://developers.google.com/appengine/downloads

### Running server

  * From the root directory of this repository, run:

        dev_appserver.py app

  * Open your browser to <http://localhost:8080/> to see that it works.

### Running tests

  * To run tests, run:

        ./test.py

### Publishing packages locally

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

## Deploying to the web

See the docs on [branches and versions][].

[branches and versions]: https://github.com/dart-lang/pub-dartlang/wiki/Branches-and-Versions

## Modifying the CSS and documentation

* The [CSS files](app/static/style.css) are generated from the source [Sass][] files using [Compass][].

* The [HTML documentation files](app/views/doc/) are generated from the source [Markdown][] using
[Jekyll][].

To get ready to make changes, you'll need [Ruby][] and [Python][].
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

This is only needed on your development machine to iterate on the CSS
and documentation. The deployed server just uses the pre-compiled CSS and HTML
and only requires Python.

Once you have everything installed, to modify the styles and documentation:

 1. Run [Foreman][] to automatically regenerate the CSS and HTML files when any
    Sass or Markdown files change:

        bundle exec foreman start

 1. Edit the `.scss` files under `css/sass` and the `.markdown` files under
    `doc`.

[foreman]: http://ddollar.github.com/foreman/

**When you make changes to SCSS or Markdown files, make sure to check in the
generated CSS or HTML files with them.**
