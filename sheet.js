/* CAR DEALER — A4 lista za auto, optimized for BLACK & WHITE laser printing.
   No filled areas: black type, black rules, outlined boxes. One renderer for the web page and the PDF.
   renderSheet(car) -> HTML of one A4 page; SHEET_CSS -> its styles; fitSheet(root) -> shrinks lists to fit.
   Needs logo_data.js (window.CD_LOGO.black). car.qr_svg = QR of the ad, car.qr_dealer_svg = QR of the full offer. */
(function () {
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var CHECK = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="1" width="14" height="14" rx="2" fill="none" stroke="#000" stroke-width="1.6"/><path d="M4.2 8.3l2.6 2.6 5-5.4" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var DOT = '<svg viewBox="0 0 8 8" aria-hidden="true"><rect x="2" y="2" width="4" height="4" fill="#000"/></svg>';
  var MAX_EQ = 40, MAX_SAFE = 9;
  var SERVICES = [
    "Kupovina na kredit i lizing",
    "Provera u ovlašćenim servisima",
    "Garancija na legalnost, kilometražu, motor i menjač",
    "Tehnički pregled, registracija i probne tablice",
    "Zamena i otkup vozila"
  ];

  window.SHEET_CSS = [
    ".a4{--ink:#000;--soft:#333;--rule:#000;--hair:#8a8a8a;",
    "width:210mm;height:297mm;box-sizing:border-box;background:#fff;color:var(--ink);font-family:Poppins,'Segoe UI',Arial,sans-serif;",
    "display:flex;flex-direction:column;overflow:hidden;position:relative;padding:0 12mm}",
    ".a4 *{box-sizing:border-box}",
    ".a4 .hd{display:flex;align-items:center;justify-content:space-between;padding:6mm 0 3mm;border-bottom:2.2pt solid var(--rule)}",
    ".a4 .hd img{width:40mm;height:auto;display:block}",
    ".a4 .hd .meta{text-align:right;font-size:8.5pt;color:var(--soft);line-height:1.55}",".a4 .hd .right{display:flex;align-items:center;gap:4mm}",".a4 .hd .dq{display:flex;align-items:center;gap:2.4mm;border-left:.8pt solid var(--hair);padding-left:4mm}",".a4 .hd .dq .box{width:19mm;height:19mm;border:1pt solid var(--ink);border-radius:1.5mm;padding:.8mm}",".a4 .hd .dq .box svg{width:100%;height:100%;display:block}",".a4 .hd .dq b{display:block;font-size:7.6pt;letter-spacing:.16em;line-height:1.3}",".a4 .hd .dq span{display:block;font-size:7pt;color:var(--soft);line-height:1.3}",
    ".a4 .hd .meta b{display:block;font-size:10pt;letter-spacing:.24em;color:var(--ink);font-weight:700}",
    ".a4 .hero{display:flex;justify-content:space-between;align-items:center;gap:6mm;padding:3.5mm 0 3.5mm}",
    ".a4 .make{font-size:10.5pt;letter-spacing:.34em;font-weight:600;text-transform:uppercase}",
    ".a4 .model{font-size:34pt;font-weight:700;line-height:1;margin:1.2mm 0 1.6mm;letter-spacing:-.01em}",
    ".a4 .variant{font-size:12pt;color:var(--soft)}",
    ".a4 .price{flex:none;border:2.2pt solid var(--ink);border-radius:3mm;padding:2.4mm 5mm 2.6mm;text-align:center;min-width:60mm}",
    ".a4 .price .lbl{font-size:8.5pt;letter-spacing:.34em;font-weight:600}",
    ".a4 .price .val{font-size:31pt;font-weight:700;line-height:1.08;white-space:nowrap}",
    ".a4 .price .note{font-size:8pt;color:var(--soft)}",
    ".a4 .price .tags{font-size:8pt;margin-top:1.4mm;border-top:.8pt solid var(--hair);padding-top:1.4mm}",
    ".a4 .specs{display:grid;grid-template-columns:repeat(4,1fr);border-top:1.2pt solid var(--rule);border-bottom:1.2pt solid var(--rule)}",
    ".a4 .spec{padding:1.7mm 2.4mm 1.7mm 0;border-bottom:.6pt solid var(--hair)}",
    ".a4 .spec:nth-child(4n+2),.a4 .spec:nth-child(4n+3),.a4 .spec:nth-child(4n+4){padding-left:3mm;border-left:.6pt solid var(--hair)}",
    ".a4 .spec:nth-last-child(-n+4){border-bottom:0}",
    ".a4 .spec .k{font-size:7pt;letter-spacing:.16em;text-transform:uppercase;color:var(--soft)}",
    ".a4 .spec .v{font-size:9.8pt;font-weight:600;line-height:1.25;margin-top:.4mm}",
    ".a4 .hl{display:flex;flex-wrap:wrap;gap:1.6mm;align-items:center;padding:3mm 0 0}",
    ".a4 .hl .t{font-size:8pt;letter-spacing:.24em;font-weight:700;margin-right:1mm}",
    ".a4 .hl span.p{border:1pt solid var(--ink);font-weight:600;font-size:8.2pt;border-radius:9mm;padding:.5mm 2.8mm}",
    ".a4 .body{margin-top:3.5mm;flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;gap:4mm;--k:1}",
    ".a4 .row3{display:grid;grid-template-columns:1fr 1fr 1.15fr;gap:6mm}",
    ".a4 h3{font-size:8.5pt;letter-spacing:.24em;font-weight:700;margin:0 0 1.8mm;padding-bottom:1.3mm;border-bottom:1.2pt solid var(--rule)}",
    ".a4 ul{list-style:none;margin:0;padding:0}",
    ".a4 .eq{columns:var(--cols,4);column-gap:4mm}",
    ".a4 li{font-size:calc(8.4pt * var(--k,1));line-height:1.34;display:flex;gap:1.6mm;align-items:baseline;break-inside:avoid;padding:.2mm 0}",
    ".a4 li svg{width:2.2mm;height:2.2mm;flex:none;transform:translateY(.1mm)}",
    ".a4 li.more{font-weight:700}",".a4 .chk li{font-size:calc(9pt * var(--k,1));font-weight:500}",
    ".a4 .chk li svg{width:2.9mm;height:2.9mm;transform:translateY(.45mm)}",
    ".a4 .desc{margin:0;font-size:calc(8.8pt * var(--k,1));line-height:1.5;color:var(--soft)}",
    ".a4 .ft{margin-top:3mm;border-top:2.2pt solid var(--rule);padding:3.5mm 0 6.5mm;display:grid;grid-template-columns:1fr auto;gap:8mm;align-items:start}",
    ".a4 .ft h4{margin:0 0 1.8mm;font-size:8.5pt;letter-spacing:.24em;font-weight:700}",
    ".a4 .ft ul li{font-size:8.2pt}",
    ".a4 .ft .addr{margin-top:2.2mm;font-size:10pt;font-weight:700}",
    ".a4 .ft .addr small{display:block;font-weight:400;font-size:8.5pt;color:var(--soft)}",
    ".a4 .qr{text-align:center;width:31mm}",
    ".a4 .qr .box{border:1pt solid var(--ink);border-radius:2mm;padding:1mm;width:31mm;height:31mm}",
    ".a4 .qr .box svg{width:100%;height:100%;display:block}",
    ".a4 .qr b{display:block;margin-top:1.6mm;font-size:8pt;letter-spacing:.16em}",
    ".a4 .qr span{display:block;font-size:7.2pt;color:var(--soft);line-height:1.3}",
    ".a4 .slogan{position:absolute;left:12mm;right:12mm;bottom:3mm;text-align:center;font-size:6.8pt;letter-spacing:.42em;color:var(--soft)}"
  ].join("");

  window.fitSheet = function (root) {
    var b = (root || document).querySelector(".a4 .body"); if (!b) return;
    var over = function () { return b.scrollHeight > b.clientHeight + 1; };
    var k;
    for (k = 1; k >= 0.82; k -= 0.02) { b.style.setProperty("--k", k.toFixed(2)); if (!over()) break; }
    /* still too long: drop equipment items from the end and say how many more are in the ad */
    var ul = b.querySelector(".eq");
    if (ul && over()) {
      var total = +ul.getAttribute("data-total") || 0, more = ul.querySelector("li.more");
      if (!more) { more = document.createElement("li"); more.className = "more"; more.appendChild(document.createElement("span")); ul.appendChild(more); }
      var items = function () { return ul.querySelectorAll("li:not(.more)"); };
      while (over() && items().length > 8) {
        var it = items(); it[it.length - 1].remove();
        more.firstChild.textContent = "+ još " + (total - items().length) + " stavki opreme u oglasu (QR kod)";
      }
    }
    return { k: +k.toFixed(2), fits: !over(), shown: ul ? ul.querySelectorAll("li:not(.more)").length : 0 };
  };

  window.renderSheet = function (car) {
    var L = window.CD_LOGO || {};
    var specs = (car.specs || []).filter(function (s) { return s[1] && s[1] !== "—"; }).slice(0, 16);
    while (specs.length % 4) specs.push(["", ""]);
    var li = function (arr, icon) {
      return (arr || []).map(function (s) { return "<li>" + icon + "<span>" + esc(s) + "</span></li>"; }).join("");
    };
    var tags = [];
    if (car.trade_in) tags.push("Zamena: " + car.trade_in);
    if (car.fixed_price) tags.push("Fiksna cena: " + car.fixed_price);
    var qr = function (svg, title, sub) {
      return svg ? '<div class="qr"><div class="box">' + svg + "</div><b>" + title + "</b><span>" + sub + "</span></div>" : "";
    };
    return '<article class="a4">' +
      '<header class="hd"><img src="' + (L.black || L.blue || "") + '" alt="CAR DEALER">' +
      '<div class="right"><div class="meta"><b>U PONUDI</b>Oglas br. ' + esc(car.id) + (car.published ? "<br>Objavljen " + esc(car.published) : "") + "</div>" +
      (car.qr_dealer_svg ? '<div class="dq"><div class="box">' + car.qr_dealer_svg + '</div><div><b>CELA<br>PONUDA</b><span>svi naši<br>automobili</span></div></div>' : "") +
      "</div></header>" +
      '<section class="hero"><div><div class="make">' + esc(car.make) + '</div><div class="model">' + esc(car.model) +
      "</div>" + (car.variant ? '<div class="variant">' + esc(car.variant) + "</div>" : "") + "</div>" +
      (car.price ? '<div class="price"><div class="lbl">CENA</div><div class="val">' + esc(car.price) + "</div>" +
        (car.price_note ? '<div class="note">' + esc(car.price_note) + "</div>" : "") +
        (tags.length ? '<div class="tags">' + esc(tags.join("   ·   ")) + "</div>" : "") + "</div>" : "") +
      "</section>" +
      '<section class="specs">' + specs.map(function (s) {
        return '<div class="spec"><div class="k">' + esc(s[0]) + '</div><div class="v">' + esc(s[1]) + "</div></div>";
      }).join("") + "</section>" +
      ((car.highlights || []).length ? '<section class="hl"><span class="t">ISTAKNUTO</span>' +
        car.highlights.slice(0, 5).map(function (h) { return '<span class="p">' + esc(h) + "</span>"; }).join("") + "</section>" : "") +
      '<section class="body">' +
      ((car.equipment || []).length ? '<div><h3>OPREMA</h3><ul class="eq" data-total="' + car.equipment.length + '">' + li(car.equipment.slice(0, MAX_EQ), DOT) +
        (car.equipment.length > MAX_EQ ? '<li class="more"><span>+ još ' + (car.equipment.length - MAX_EQ) + " stavki opreme u oglasu (QR kod)</span></li>" : "") +
        "</ul></div>" : "") +
      '<div class="row3">' +
      ((car.condition || []).length ? '<div><h3>STANJE</h3><ul class="chk">' + li(car.condition, CHECK) + "</ul></div>" : "<div></div>") +
      ((car.safety || []).length ? '<div><h3>SIGURNOST</h3><ul>' + li(car.safety.slice(0, car.safety.length > MAX_SAFE + 2 ? MAX_SAFE : 99), DOT) + (car.safety.length > MAX_SAFE + 2 ? '<li class="more"><span>+ još ' + (car.safety.length - MAX_SAFE) + "</span></li>" : "") + "</ul></div>" : "<div></div>") +
      (car.note ? '<div><h3>O VOZILU</h3><p class="desc">' + esc(car.note) + "</p></div>" : "<div></div>") +
      "</div></section>" +
      '<footer class="ft"><div><h4>CAR DEALER VAM OMOGUĆAVA</h4><ul class="chk">' + li(SERVICES, CHECK) + "</ul>" +
      '<div class="addr">' + esc(car.address || "Beograd · Marka Čelebonovića 18") +
      "<small>" + esc(car.contact_line || "Molimo vas da se najavite pre dolaska") + "</small></div></div>" +
      qr(car.qr_svg, "SKENIRAJ OGLAS", "sve fotografije i detalji<br>ovog automobila") +
      "</footer>" +
      '<div class="slogan">DON\'T DREAM IT, DRIVE IT</div>' +
      "</article>";
  };
})();
