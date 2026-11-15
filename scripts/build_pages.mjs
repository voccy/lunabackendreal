// Prepare only browser assets. Raster binaries remain in the Python science service.
import { cpSync, copyFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
const project = process.cwd();
const output = join(project, 'public');
rmSync(output, { recursive: true, force: true });
mkdirSync(join(output, 'data'), { recursive: true });
for (const file of ['index.html', 'app.js', 'terrain-webgl.js', 'style.css', 'site01.css']) copyFileSync(join(project, file), join(output, file));
for (const file of ['site01-preview-grid.json', 'site01-center-point.json', 'site01_relief.png']) copyFileSync(join(project, 'data', file), join(output, 'data', file));
console.log('Cloudflare Pages static output: public/ (no large GeoTIFFs). Pages Functions remain in functions/.');
