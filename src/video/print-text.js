/* Print text onto a product photo: fit-to-box inside a measured print area (src/video/print-areas.json), mapped to the
   quad with matrix3d so it follows the surface perspective, wrapped on round surfaces (curve), clipped to the product's
   own alpha so it can never leave the product, and finished with a print look (multiply ink, 0.92 opacity, a 0.3px
   blur and the fabric's shading over it). Shared by everything that prints text on a product photo (the hero video src/video/hero-promo.html, its checks). */
(function (global) {
  // homography: maps the unit square to the quad (four [x, y] points, clockwise from top-left)
  function squareToQuad(q) {
    var x0 = q[0][0], y0 = q[0][1], x1 = q[1][0], y1 = q[1][1], x2 = q[2][0], y2 = q[2][1], x3 = q[3][0], y3 = q[3][1];
    var dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3, dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
    var det = dx1 * dy2 - dx2 * dy1, g = (dx3 * dy2 - dx2 * dy3) / det, h = (dx1 * dy3 - dx3 * dy1) / det;
    return [x1 - x0 + g * x1, x3 - x0 + h * x3, x0, y1 - y0 + g * y1, y3 - y0 + h * y3, y0, g, h, 1];
  }
  function matrix3d(w, h, quadPx) {           // a w x h element onto quadPx
    var m = squareToQuad(quadPx);
    var a = m[0] / w, b = m[1] / h, c = m[2], d = m[3] / w, e = m[4] / h, f = m[5], g = m[6] / w, k = m[7] / h;
    return 'matrix3d(' + [a, d, 0, g, b, e, 0, k, 0, 0, 1, 0, c, f, 0, 1].map(function (v) { return +v.toFixed(8); }).join(',') + ')';
  }
  /* place(stage, area, text, opts): stage = the element that holds the product <img> at a known square size.
     opts: color, font (CSS family), weight, minPx, pad (0.08), image (URL of the product, for the mask and shading),
     layer (print into this element), maxLines (overrides the area's) */
  function place(stage, area, text, opts) {
    opts = opts || {};
    var S = stage.clientWidth, q = area.quad.map(function (p) { return [p[0] * S, p[1] * S]; });
    var w = Math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]), h = Math.hypot(q[3][0] - q[0][0], q[3][1] - q[0][1]);
    var layer = opts.layer || stage.querySelector('.pt-layer');      // opts.layer: an element of yours to print into (several per product)
    if (!layer) { layer = document.createElement('div'); stage.appendChild(layer); }
    if (!layer.querySelector('.pt-box')) {
      layer.classList.add('pt-layer');
      layer.innerHTML = '<div class="pt-box"><div class="pt-text" data-on-product></div></div><div class="pt-shade"></div>';
    }
    var mask = 'url("' + opts.image + '")';
    layer.style.cssText = 'position:absolute;inset:0;pointer-events:none;-webkit-mask-image:' + mask + ';mask-image:' + mask +
      ';-webkit-mask-size:100% 100%;mask-size:100% 100%;';
    var box = layer.querySelector('.pt-box'), t = layer.querySelector('.pt-text'), shade = layer.querySelector('.pt-shade');
    box.style.cssText = 'position:absolute;left:0;top:0;width:' + w + 'px;height:' + h + 'px;transform-origin:0 0;display:grid;place-items:center;' +
      'transform:' + matrix3d(w, h, q) + ';';
    var pad = (opts.pad == null ? 0.08 : opts.pad);
    t.style.cssText = 'max-width:' + (w * (1 - 2 * pad)) + 'px;text-align:center;line-height:1.02;letter-spacing:-0.02em;font-family:' + (opts.font || 'Geist, Inter, sans-serif') +
      ';font-weight:' + (opts.weight || 700) + ';color:' + (opts.color || '#1F2937') + ';mix-blend-mode:' + (area.ink || 'multiply') + ';opacity:.92;filter:blur(.3px);overflow-wrap:normal;';
    var maxLines = opts.maxLines || area.maxLines || 2;
    if (maxLines === 1) t.style.whiteSpace = 'nowrap';   // one-line areas (the cap) never wrap
    // words never break inside; on round surfaces each letter is its own span so it can be wrapped onto the curve
    t.textContent = '';
    text.split(' ').forEach(function (word, i) {
      if (i) t.appendChild(document.createTextNode(' '));
      var w_ = document.createElement('span'); w_.style.whiteSpace = 'nowrap'; w_.style.display = 'inline-block';
      if (area.curve) word.split('').forEach(function (ch) { var c = document.createElement('span'); c.className = 'pt-ch'; c.textContent = ch; c.style.display = 'inline-block'; w_.appendChild(c); });
      else w_.textContent = word;
      t.appendChild(w_);
    });
    // fit-to-box: the largest size whose lines (at most maxLines) fit inside the box minus the padding
    var lo = opts.minPx || 6, hi = h, best = lo, maxW = w * (1 - 2 * pad), maxH = h * (1 - 2 * pad), lineH;
    for (var i = 0; i < 24; i++) {
      var mid = (lo + hi) / 2; t.style.fontSize = mid + 'px'; lineH = mid * 1.02;
      var lines = new Set([].map.call(t.children, function (w_) { return w_.offsetTop; })).size, fits = t.scrollWidth <= maxW + 0.5 && t.scrollHeight <= maxH + 0.5 && lines <= maxLines;
      if (fits) { best = mid; lo = mid; } else hi = mid;
    }
    t.style.fontSize = best + 'px';
    // wrap on round surfaces: letters near the edges are compressed and pulled in, like print on a cylinder
    if (area.curve) {
      t.style.position = 'relative';
      var spans = [].slice.call(t.querySelectorAll('.pt-ch')), half = t.clientWidth / 2 || 1, th = Math.acos(1 - area.curve) || 0.0001;
      spans.forEach(function (s) {                                              // layout positions, before the perspective
        var u = (s.offsetLeft + s.parentNode.offsetLeft + s.offsetWidth / 2 - half) / half;   // -1..1 across the text
        var x = Math.sin(u * th) / Math.sin(th), scale = Math.cos(u * th);
        s.style.transform = 'translateX(' + ((x - u) * half).toFixed(2) + 'px) scaleX(' + scale.toFixed(3) + ')';
      });
    }
    // the fabric's shading over the ink, so it reads as printed
    shade.style.cssText = 'position:absolute;inset:0;background:' + mask + ' center/100% 100% no-repeat;mix-blend-mode:soft-light;opacity:.35;';
    return { fontPx: best, quadPx: q, boxW: w, boxH: h };
  }
  global.PrintText = { place: place, matrix3d: matrix3d };
})(window);
