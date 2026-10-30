// usage: node qr.js <text>  -> prints an SVG QR code (uses the QR encoder bundled with npm)
const path = require('path');
const base = process.env.QR_LIB || '/opt/node22/lib/node_modules/npm/node_modules/qrcode-terminal/vendor/QRCode';
const QRCode = require(base);
const QRErrorCorrectLevel = require(path.join(base, 'QRErrorCorrectLevel'));
const q = new QRCode(-1, QRErrorCorrectLevel.M);
q.addData(process.argv[2]); q.make();
const n = q.getModuleCount(), m = 2; let d = '';
for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c + m} ${r + m}h1v1h-1z`;
process.stdout.write(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n + 2 * m} ${n + 2 * m}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="#fff"/><path d="${d}" fill="#000"/></svg>`);
