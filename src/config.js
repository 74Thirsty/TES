import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const defaultDataPath = fileURLToPath(new URL('../data/tes-data.json', import.meta.url));

export const config = {
  port: 4000,
  env: 'development',
  dataFile: defaultDataPath,
  dataDirectory: dirname(defaultDataPath)
};

export function loadConfigFromEnv () {
  const portValue = Number.parseInt(process.env.PORT ?? '4000', 10);
  config.port = Number.isFinite(portValue) ? portValue : 4000;
  config.env = process.env.NODE_ENV ?? 'development';

  const configuredPath = process.env.TES_DB_FILE;
  if (!configuredPath || configuredPath.length === 0) {
    config.dataFile = defaultDataPath;
  } else if (configuredPath === ':memory:') {
    config.dataFile = ':memory:';
  } else if (configuredPath.startsWith('file://')) {
    config.dataFile = fileURLToPath(configuredPath);
  } else if (configuredPath.startsWith('/')) {
    config.dataFile = configuredPath;
  } else {
    config.dataFile = resolve(process.cwd(), configuredPath);
  }

  config.dataDirectory = config.dataFile === ':memory:' ? null : dirname(config.dataFile);
}

loadConfigFromEnv();
