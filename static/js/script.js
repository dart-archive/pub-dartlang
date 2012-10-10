/* Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
 * for details. All rights reserved. Use of this source code is governed by a
 * BSD-style license that can be found in the LICENSE file. */

$(function() {
  $("article").find("h2, h3, h4").each(function() {
    $(this).append($('<a class="permalink" title="Permalink" href="#' + $(this).attr('id') + '">#</a>'));
  });

  // Allow the anchor to specify which tab of a tabbed control is shown.
  if (window.location.hash !== "") {
    $('a[href="' + window.location.hash + '"][data-toggle="tab"]').tab('show');
  }
});
