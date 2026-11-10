/** Preserve the host test runner's normal cwd inside an owned diagnostic Job. */
import {fileURLToPath} from 'node:url';
process.chdir(fileURLToPath(new URL('../../apps/host/', import.meta.url)));
