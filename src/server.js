import { config } from './config.js';
import { createAppServer } from './app.js';
import { initStorage } from './storage.js';

await initStorage();

const server = createAppServer();
server.listen(config.port, () => {
  console.info(`TES API listening on port ${config.port}`);
});

process.on('SIGINT', () => {
  server.close(() => process.exit(0));
});
