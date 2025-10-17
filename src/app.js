import { createServer } from 'node:http';
import { handleRequest } from './router.js';

export function createAppServer () {
  return createServer((req, res) => {
    handleRequest(req, res);
  });
}
