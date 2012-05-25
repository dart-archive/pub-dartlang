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

* Install the [App Engine
  SDK](https://developers.google.com/appengine/downloads).
* Make sure the SDK is on your `$PATH`.
* Run `dev_appserver.py .` from the root directory of this repository.

That's it. All the dependencies needed to run the app are included in the
repository so that App Engine can use them, so no further installation is
necessary.

### Running Tests

The tests do have some external dependencies. To run the tests, perform the
following steps:

* Install the [App Engine
  SDK](https://developers.google.com/appengine/downloads).
* Make sure the SDK is on your `$PATH`.
* Run `easy_install webtest`.
* Run `easy_install beautifulsoup4`.
* Run `./test.py`.
