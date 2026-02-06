const http = require('http');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, 'public');
const map = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
};

http.createServer((req, res) => {
  let reqPath = req.url.split('?')[0];
  if (reqPath === '/') reqPath = '/index.html';
  const file = path.normalize(path.join(root, reqPath));

  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': map[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(8080, '0.0.0.0', () => {
  console.log('Server running at http://0.0.0.0:8080');
});
