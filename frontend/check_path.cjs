const fs = require('fs');
const path = require('path');

const p1 = path.resolve(__dirname, 'src/socket.js');
console.log('socket.js path:', p1);

const p2 = path.resolve(__dirname, '../../../../sites/common_site_config.json');
console.log('4 levels up:', p2, fs.existsSync(p2));

const p3 = path.resolve(__dirname, '../../../../../sites/common_site_config.json');
console.log('5 levels up:', p3, fs.existsSync(p3));
