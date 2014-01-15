/* Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
 * for details. All rights reserved. Use of this source code is governed by a
 * BSD-style license that can be found in the LICENSE file. */

$(function() {
  $("section").find("h1, h2, h3, h4").each(function() {
    // Sets the IDs on headings that are in user provided markdown.
    if (!$(this).attr('id')) {
      $(this).attr('id', $(this).text());
    }

    id = $(this).attr('id');

    // Add a hash link to every heading.
    $(this).append(
        $('<a class="permalink" title="Permalink" href="#' + id + '">#</a>'));

    if (!$(this).is('.no-nav-link')) {
      // Section will be "readme", or "changelog",
      // or whatever other section this heading is under.
      section = $(this).parent().attr('id');
      $('li' + '.' + section + ' ol').append(
          $('<li>' +
              '<a href="#' + id + '">' + id + '</a>' +
            '</li>'));
    }

  });

  // Allow the anchor to specify which tab of a tabbed control is shown.
  if (window.location.hash !== "") {
    $('a[href="' + window.location.hash + '"][data-toggle="tab"]').tab('show');
  }

  var reload = $(".admin .reload");
  if (reload.length != 0) {
    var reloadInterval = setInterval(function() {
      $.ajax({
        url: "/packages/versions/reload.json",
        dataType: "json"
      }).done(function(data) {
        if (data['done']) {
          clearInterval(reloadInterval);
          reload.find(".progress .bar").css("width", "100%");
          reload.find(".progress").removeClass("active");
          reload.find("h3").text("All packages reloaded")
          return;
        }

        reload.find(".count").text(data["count"]);
        reload.find(".total").text(data["total"]);
        var percentage = (100 * data["count"]/data["total"]) + '%';
        reload.find(".progress .bar").css("width", percentage);
      });
    }, 1000);
  }
});
