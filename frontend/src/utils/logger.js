// Minimalny, spójny logger do frontendu (bez emoji)
// - Prefiks: [TK]
// - Działa tylko w trybie development (unikamy szumu w produkcji)
// - Brak emoji ani ozdobników

const isDev = typeof import.meta !== 'undefined' ? import.meta.env?.DEV : process.env.NODE_ENV !== 'production';

function formatArgs(args) {
  try {
    // Płaski format bez specjalnych styli
    return args;
  } catch {
    return args;
  }
}

const prefix = '[TK]';

export const logger = {
  debug: (...args) => {
    if (!isDev) return;
    // eslint-disable-next-line no-console
    console.debug(prefix, ...formatArgs(args));
  },
  info: (...args) => {
    if (!isDev) return;
    // eslint-disable-next-line no-console
    console.info(prefix, ...formatArgs(args));
  },
  warn: (...args) => {
    if (!isDev) return;
    // eslint-disable-next-line no-console
    console.warn(prefix, ...formatArgs(args));
  },
  error: (...args) => {
    if (!isDev) return;
    // eslint-disable-next-line no-console
    console.error(prefix, ...formatArgs(args));
  },
};

export default logger;

